# CLAUDE.md - Guidelines for AI Assistants

## Build and Test Commands
- Install: `uv pip install -e .`
- Run tests: `pytest`
- Run single test: `pytest tests/test_git_summarizer.py::test_name`
- Run the tool: `python -m src.git_summarizer` or `git-ai` (if installed)

## Code Style Guidelines
- **Formatting**: Follow PEP 8, with 4 spaces for indentation
- **Imports**: Group standard lib, third-party, local imports; alphabetize
- **Types**: Use type annotations for function parameters and return values
- **Naming**: 
  - Functions/variables: snake_case
  - Classes: PascalCase
  - Constants: UPPER_CASE
- **Error handling**: Use try/except blocks with specific exceptions
- **Documentation**: Docstrings for all functions with param/return descriptions
- **Performance**: Ensure code scales linearly with repo size and complexity
- **Compatibility**: Maintain compatibility with Python 3.6+

## Repository Structure
- `src/`: Source code for the Git AI tool
- `tests/`: Unit tests
- `setup.py`: Package configuration
- `README.md`: Documentation
- `LICENSE`: MIT License