import asyncio
from pydantic import BaseModel, Field
from ollama import chat

# Import your pipeline modules
from app.retrieval.search import hybrid_search
from app.generation.generator import generate_response_stream

# Define the Structured Output Schema for the Judge
class EvaluationMetrics(BaseModel):
    faithfulness: float = Field(description="Score from 0.0 to 1.0. Is the response derived purely from the retrieved context without hallucination?")
    context_relevance: float = Field(description="Score from 0.0 to 1.0. Are the retrieved chunks actually relevant to answering the user input?")
    answer_relevance: float = Field(description="Score from 0.0 to 1.0. Does the generated response directly and fully address the user input?")
    reasoning: str = Field(description="A brief, one-sentence justification for the given scores.")

# 1. Your production evaluation dataset
eval_dataset = [
    {"question": "What is the refund policy within 14 days?", "ground_truth": "Customers can request a full refund within 14 days of their original purchase date."},
    {"question": "Can I get a refund after 20 days?", "ground_truth": "Requests made between 15 and 30 days are eligible only for store credit. No refunds are issued."},
    {"question": "What happens if I request a return after 35 days?", "ground_truth": "No refunds or credits are issued after 30 days."},
    {"question": "Do you accept returns without a receipt?", "ground_truth": "Returns always require a valid receipt or proof of purchase."},
    {"question": "Can I exchange an item instead of getting store credit?", "ground_truth": "Yes, items can be exchanged for an identical item or value within 30 days."}
]

# 2. Async helper to collect generator stream chunks
async def aggregate_stream(query: str) -> str:
    full_text = ""
    for chunk in generate_response_stream(query):
        full_text += chunk
    return full_text

# 3. Local judge evaluator with forced 0.0 - 1.0 scaling
def evaluate_row_local(user_input: str, context: list, response: str, reference: str) -> EvaluationMetrics:
    judge_prompt = f"""
    You are an expert AI Judge evaluating a Retrieval-Augmented Generation (RAG) system.
    Analyze the alignment between the Input, Retrieved Context, Generated Response, and Ground Truth Reference.

    CRITICAL INSTRUCTION: You must score strictly using decimal floats between 0.0 and 1.0 (e.g., 0.0, 0.5, 1.0). 
    Do NOT use integer scales like 1-5 or 1-10. A perfect score is 1.0. A completely failing score is 0.0.

    [User Input]: {user_input}
    [Retrieved Context]: {chr(10).join(context)}
    [Generated Response]: {response}
    [Ground Truth Reference]: {reference}
    """

    result = chat(
        model='phi3',
        messages=[{'role': 'user', 'content': judge_prompt}],
        format=EvaluationMetrics.model_json_schema(),
        options={'temperature': 0.0}
    )
    
    return EvaluationMetrics.model_validate_json(result.message.content)

# 4. Main orchestration loop
async def run_evaluation():
    print("🚀 Starting local pipeline evaluation...")
    results = []
    
    for idx, item in enumerate(eval_dataset):
        query = item["question"]
        print(f"\n[Processing Case {idx+1}/{len(eval_dataset)}]: '{query}'")
        
        # Retrieve chunks
        retrieved_chunks = hybrid_search(query, top_k=3)
        context_strings = [chunk.get("text", chunk.get("content", "")) for chunk in retrieved_chunks] 
        
        # Generate response using your pipeline stream (with a 3-strike retry loop for 503 errors)
        generated_answer = ""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                generated_answer = await aggregate_stream(query)
                break  # Successful generation, exit the retry loop
            except Exception as e:
                if "503" in str(e) and attempt < max_retries - 1:
                    print(f"⚠️ Gemini experiencing high demand (503). Retrying in 2 seconds... (Attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(2)
                else:
                    print(f"❌ Generation failed completely for case {idx+1}: {e}")
                    break
        
        # Skip grading if the generation failed completely after all retries
        if not generated_answer:
            continue
            
        # Grade using local Ollama model
        try:
            scores = evaluate_row_local(
                user_input=query,
                context=context_strings,
                response=generated_answer,
                reference=item["ground_truth"]
            )
            results.append(scores)
            print("✅ Graded successfully.")
            print(f" -> Scores -> Faithfulness: {scores.faithfulness} | Context: {scores.context_relevance} | Answer: {scores.answer_relevance}")
        except Exception as e:
            print(f"❌ Grading failed for case {idx+1}: {e}")

    # Final Aggregations
    if results:
        avg_faithfulness = sum(r.faithfulness for r in results) / len(results)
        avg_context_rel = sum(r.context_relevance for r in results) / len(results)
        avg_answer_rel = sum(r.answer_relevance for r in results) / len(results)

        print("\n================ FINAL METRICS ================")
        print(f"Faithfulness Score:        {avg_faithfulness:.2f}")
        print(f"Context Relevance Score:   {avg_context_rel:.2f}")
        print(f"Answer Relevance Score:    {avg_answer_rel:.2f}")
        print("===============================================")

if __name__ == "__main__":
    asyncio.run(run_evaluation())