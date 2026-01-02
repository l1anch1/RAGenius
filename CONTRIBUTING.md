# Contributing to RAGenius

Thank you for your interest in contributing to RAGenius! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/l1anch1/DeepSeek-RAG/issues)
2. If not, create a new issue using the Bug Report template
3. Provide detailed information including:
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details
   - Relevant logs or screenshots

### Suggesting Features

1. Check if the feature has already been requested
2. Create a new issue using the Feature Request template
3. Clearly describe:
   - The problem you're trying to solve
   - Your proposed solution
   - Use cases and benefits

### Pull Requests

#### Before You Start

1. **Fork the repository** and create your branch from `main`
2. **Check existing PRs** to avoid duplicate work
3. **Open an issue first** for major changes to discuss the approach

#### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/DeepSeek-RAG.git
cd RAGenius

# Add upstream remote
git remote add upstream https://github.com/l1anch1/DeepSeek-RAG.git

# Create a feature branch
git checkout -b feature/your-feature-name

# Install dependencies
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..

# Install development tools
pip install black flake8 pylint isort
```

#### Making Changes

1. **Follow the code style**:
   - Python: Black (line length 100), Flake8, Pylint
   - JavaScript: ESLint with project config
   - Use meaningful variable and function names
   - Add comments for complex logic

2. **Write tests** (when applicable):
   - Add unit tests for new functions
   - Ensure existing tests pass
   - Aim for good test coverage

3. **Update documentation**:
   - Update README.md if needed
   - Add docstrings to new functions/classes
   - Update configuration documentation

4. **Commit guidelines**:
   ```bash
   # Use conventional commits format
   git commit -m "feat: add new retrieval stage"
   git commit -m "fix: resolve memory leak in cache manager"
   git commit -m "docs: update installation instructions"
   git commit -m "refactor: simplify query expansion logic"
   ```

   Commit types:
   - `feat`: New feature
   - `fix`: Bug fix
   - `docs`: Documentation changes
   - `style`: Code style changes (formatting, etc.)
   - `refactor`: Code refactoring
   - `perf`: Performance improvements
   - `test`: Adding or updating tests
   - `chore`: Maintenance tasks
   - `ci`: CI/CD changes

#### Running Tests Locally

```bash
# Backend tests
cd backend
python -m py_compile app.py
flake8 . --exclude=models_cache,__pycache__
black --check .

# Frontend tests
cd frontend
npm run lint
npm run build

# Docker build test
docker-compose build
```

#### Submitting Your PR

1. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request**:
   - Use the PR template
   - Link related issues
   - Provide clear description of changes
   - Add screenshots for UI changes

3. **Address review feedback**:
   - Respond to comments
   - Make requested changes
   - Push updates to the same branch

4. **Wait for CI checks**:
   - All CI checks must pass
   - Fix any failing tests or linting issues

## Code Style Guidelines

### Python

```python
# Good
def calculate_similarity_score(
    query_embedding: np.ndarray,
    document_embedding: np.ndarray,
    method: str = "cosine"
) -> float:
    """
    Calculate similarity score between query and document embeddings.
    
    Args:
        query_embedding: Query vector representation
        document_embedding: Document vector representation
        method: Similarity calculation method (default: "cosine")
    
    Returns:
        Similarity score between 0 and 1
    """
    if method == "cosine":
        return cosine_similarity(query_embedding, document_embedding)
    raise ValueError(f"Unknown method: {method}")

# Bad
def calc(q,d,m="cosine"):
    if m=="cosine":
        return cosine_similarity(q,d)
```

### JavaScript/React

```javascript
// Good
const QueryInput = ({ onSubmit, isLoading }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSubmit(query);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        disabled={isLoading}
        placeholder="Ask a question..."
      />
    </form>
  );
};

// Bad
const QI = ({s,l}) => {
  const [q,sq]=useState('');
  return <form onSubmit={e=>{e.preventDefault();s(q);}}>
    <input value={q} onChange={e=>sq(e.target.value)} disabled={l}/>
  </form>
}
```

## Project Structure

```
RAGenius/
├── backend/
│   ├── config/          # Configuration files
│   ├── interfaces/      # Abstract interfaces
│   ├── managers/        # Resource managers (cache, models, etc.)
│   ├── services/        # Business logic
│   │   └── retrieval/   # Retrieval pipeline stages
│   ├── routes/          # API endpoints
│   └── app.py          # Application entry point
├── frontend/
│   └── src/
│       ├── components/  # React components
│       └── App.jsx     # Main application
└── .github/
    └── workflows/      # CI/CD workflows
```

## Development Workflow

1. **Sync with upstream**:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature
   ```

3. **Make changes and commit**:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

4. **Keep your branch updated**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

5. **Push and create PR**:
   ```bash
   git push origin feature/your-feature
   ```

## Getting Help

- 💬 Open a [Discussion](https://github.com/l1anch1/DeepSeek-RAG/discussions) for questions
- 🐛 Report bugs via [Issues](https://github.com/l1anch1/DeepSeek-RAG/issues)
- 📧 Email: asherlii@outlook.com

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- GitHub contributor graph

Thank you for contributing to RAGenius! 🎉

