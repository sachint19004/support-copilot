from app.retrieval.search import hybrid_search

def test_pipeline():
    query = "What is the policy on leave and cancellation?"
    print(f"Testing Hybrid Search with query: '{query}'\n")
    
    results = hybrid_search(query, top_k=2)
    
    for i, res in enumerate(results):
        print(f"--- Result {i+1} (RRF Score: {res['rrf_score']:.5f}) ---")
        print(f"Source: {res['metadata'].get('source_name')}")
        print(f"Heading: {res['metadata'].get('section_heading')}")
        print(f"Text Snippet:\n{res['text'][:150]}...\n")

if __name__ == "__main__":
    test_pipeline()