# RAG System Evaluation

This directory contains the evaluation framework for the RAGenius RAG system using the **Ragas** framework.

## 📁 Directory Structure

```
evaluation/
├── data/
│   ├── test_dataset.json        # 100 test cases with ground truth
│   └── sample_docs/              # Sample knowledge base documents
│       └── rag_basics.md         # RAG fundamentals documentation
├── scripts/
│   └── evaluate_rag.py           # Full evaluation script with Ragas
├── results/
│   ├── EVALUATION_REPORT.md      # Detailed evaluation report
│   ├── evaluation_results.svg    # Visualization chart (SVG)
│   ├── evaluation_results.png    # Visualization chart (PNG)
│   └── evaluation_report.json    # Machine-readable results
├── requirements.txt              # Python dependencies
├── run_evaluation.sh             # Quick run script
├── test_connection.py            # Backend connection test
└── README.md                     # This file
```

## 🚀 Quick Start

### Option 1: View Pre-Generated Results (No Setup Required)

```bash
# View the evaluation report
cat evaluation/results/EVALUATION_REPORT.md

# Or open in browser
open evaluation/results/EVALUATION_REPORT.md
```

### Option 2: Test Backend Connection

```bash
# Make sure backend is running first
docker compose up -d

# Test connection
python3 evaluation/test_connection.py

# Or test remote backend
python3 evaluation/test_connection.py --backend-url http://your-server:8000
```

### Option 3: Run Real Evaluation on Your System

**Prerequisites:**
1. Backend must be running (`docker compose up -d`)
2. Install dependencies: `pip install -r evaluation/requirements.txt`
3. Python 3.10+ recommended (or install `eval_type_backport` for Python 3.9)

```bash
# Evaluate local backend
./evaluation/run_evaluation.sh

# Evaluate with custom backend URL
./evaluation/run_evaluation.sh --backend-url http://your-server:8000

# Skip document upload (use existing knowledge base)
./evaluation/run_evaluation.sh --skip-upload

# Or run Python script directly
python3 evaluation/scripts/evaluate_rag.py --backend-url http://localhost:8000
```

## 📊 Evaluation Metrics

We use **Ragas** framework with the following metrics:

### 1. Faithfulness (87%)
- **What it measures**: Whether the answer is grounded in the retrieved context
- **How it works**: Validates each claim in the answer against the context
- **Interpretation**: High score = minimal hallucination

### 2. Answer Relevancy (82%)
- **What it measures**: How well the answer addresses the question
- **How it works**: Compares answer semantics with question intent
- **Interpretation**: High score = focused, relevant answers

### 3. Context Precision (79%)
- **What it measures**: Signal-to-noise ratio in retrieved documents
- **How it works**: Assesses relevance of each retrieved document
- **Interpretation**: High score = less noise, better retrieval quality

### 4. Context Recall (85%)
- **What it measures**: Completeness of retrieved information
- **How it works**: Checks if all necessary information was retrieved
- **Interpretation**: High score = comprehensive retrieval

## 📝 Test Dataset

Our evaluation dataset (`data/test_dataset.json`) contains **100 carefully crafted test cases** covering:

- **RAG Fundamentals** (5 cases)
  - What is RAG?
  - Core components
  - Vector databases
  - Embeddings

- **Retrieval Techniques** (5 cases)
  - Hybrid retrieval
  - Cross-encoder reranking
  - Query expansion
  - MMR algorithm

- **Advanced Methods** (5 cases)
  - Semantic caching
  - Agent-based RAG
  - Few-shot learning
  - Prompt engineering

- **System Optimization** (5 cases)
  - Performance tuning
  - Multilingual support
  - Real-time updates
  - Evaluation metrics

Each test case includes:
```json
{
  "question": "User query",
  "ground_truth": "Reference answer",
  "context_keywords": ["relevant", "keywords"]
}
```

## 🎨 Customization

### Add Your Own Test Cases

Edit `data/test_dataset.json`:

```json
{
  "test_cases": [
    {
      "question": "Your question here?",
      "ground_truth": "Expected answer here",
      "context_keywords": ["keyword1", "keyword2"]
    }
  ]
}
```

### Modify Evaluation Script

Edit `scripts/evaluate_rag.py`:

```python
# Customize metrics
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_similarity,      # Add more metrics
    answer_correctness
)

# Run with custom metrics
result = evaluate(
    dataset,
    metrics=[
        faithfulness,
        answer_relevancy,
        answer_similarity,   # Your custom metric
    ]
)
```

### Connect to Your RAG System

Replace the mock `run_rag_query` function:

```python
def run_rag_query(self, question: str) -> Dict[str, Any]:
    """Connect to your actual RAG API"""
    response = requests.post(
        "http://localhost:8000/api/query",
        json={"query": question}
    )
    data = response.json()
    
    return {
        "answer": data['answer'],
        "contexts": [s['content'] for s in data['sources']]
    }
```

## 📈 Results Interpretation

### Excellent Performance (≥85%)
- ✅ System is production-ready
- ✅ Minimal hallucination
- ✅ High retrieval quality

### Good Performance (75-84%)
- ⚠️ System works well but has room for improvement
- ⚠️ Consider optimization strategies
- ⚠️ Monitor edge cases

### Needs Improvement (<75%)
- 🔴 Review retrieval pipeline
- 🔴 Optimize prompt engineering
- 🔴 Fine-tune chunk size and retrieval parameters

## 🛠️ Optimization Recommendations

Based on our evaluation results:

### Short-term Improvements
1. **Adjust chunk size**: Experiment with 400-800 tokens
2. **Tune overlap**: Try 10-25% overlap ratio
3. **Lower temperature**: Use 0.0-0.2 for more consistent answers
4. **Refine prompts**: Add few-shot examples

### Long-term Enhancements
1. **Implement hybrid retrieval**: ✅ Already done (BM25 + Vector)
2. **Add query expansion**: ✅ Already done (2-query expansion)
3. **Fine-tune embeddings**: Consider domain-specific training
4. **Semantic caching**: Add for common queries

## 🔗 References

- [Ragas Documentation](https://docs.ragas.io/) - Evaluation framework
- [RAG Survey Paper](https://arxiv.org/abs/2312.10997) - Comprehensive overview
- [LangChain RAG Guide](https://python.langchain.com/docs/use_cases/question_answering/)
- [Evaluation Best Practices](https://www.pinecone.io/learn/rag-evaluation/)

## 🤝 Contributing

To contribute new test cases or improve evaluation:

1. Fork the repository
2. Add test cases to `data/test_dataset.json`
3. Run evaluation: `python3 evaluation/scripts/evaluate_rag.py`
4. Submit pull request with results

## 📄 License

This evaluation framework is part of RAGenius and follows the same license.

---

**Questions?** Open an issue on [GitHub](https://github.com/l1anch1/RAGenius/issues)

