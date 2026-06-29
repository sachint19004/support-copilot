import React, { useState, useRef, useEffect } from 'react';

export default function App() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState([
    { text: "Hello! Ask me any questions regarding company policies, refunds, or cancellations.", isUser: false }
  ]);
  const [isStreaming, setIsStreaming] = useState(false);
  const chatEndRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim() || isStreaming) return;

    const userQuery = query.trim();
    setQuery('');
    
    // 1. Add user message to screen
    setMessages(prev => [...prev, { text: userQuery, isUser: true }]);
    // 2. Add an empty bot message to prepare for streaming
    setMessages(prev => [...prev, { text: '', isUser: false }]);
    setIsStreaming(true);

    try {
      // Connect to your FastAPI backend
      const response = await fetch(`http://localhost:8000/api/chat/stream?query=${encodeURIComponent(userQuery)}`);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      // Read the stream chunk by chunk
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        
        // Append the new text chunk by cloning the last message object
        setMessages(prev => {
          const updated = [...prev];
          const lastIndex = updated.length - 1;
          
          updated[lastIndex] = { 
            ...updated[lastIndex], 
            text: updated[lastIndex].text + chunk 
          };
          
          return updated;
        });
      }
    } catch (error) {
      setMessages(prev => {
        const updated = [...prev];
        const lastIndex = updated.length - 1;
        
        updated[lastIndex] = {
          ...updated[lastIndex],
          text: "Error: Failed to connect to the backend server. Is FastAPI running?"
        };
        
        return updated;
      });
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="bg-gray-900 text-gray-100 font-sans h-screen flex flex-col">
      <header className="bg-gray-800 p-4 border-b border-gray-700 shadow-md">
        <h1 className="text-xl font-bold tracking-wide text-indigo-400">Enterprise Support Copilot</h1>
      </header>

      <main className="flex-1 overflow-y-auto p-6 space-y-4 max-w-4xl w-full mx-auto">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.isUser ? 'justify-end' : 'justify-start'}`}>
            <div className={`p-3 rounded-lg max-w-[80%] text-sm shadow whitespace-pre-wrap border ${
              msg.isUser 
                ? 'bg-gray-700 text-gray-100 border-gray-600' 
                : 'bg-indigo-900/50 text-indigo-100 border-indigo-700/50'
            }`}>
              {msg.text || (isStreaming && idx === messages.length - 1 ? "▋" : "")}
            </div>
          </div>
        ))}
        <div ref={chatEndRef} />
      </main>

      <footer className="bg-gray-800 p-4 border-t border-gray-700 shadow-lg">
        <form onSubmit={handleSubmit} className="max-w-4xl w-full mx-auto flex gap-3">
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type your question..." 
            className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-sm text-gray-100 placeholder-gray-400 focus:outline-none focus:border-indigo-500 transition-colors"
            required
            disabled={isStreaming}
          />
          <button 
            type="submit" 
            disabled={isStreaming}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-600 text-white px-6 py-3 rounded-lg text-sm font-medium transition-colors shadow-md"
          >
            {isStreaming ? 'Thinking...' : 'Send'}
          </button>
        </form>
      </footer>
    </div>
  );
}