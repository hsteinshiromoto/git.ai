# Git AI

A Python tool that summarizes git repository history and generates changelogs.

## Features

- Summarize git commits for one or all branches
- Show what files were added, modified, or deleted
- Generate detailed changelogs in Markdown format
- Group changes by date
- Written in pure Python using only standard library dependencies

## Installation

You can install Git AI using uv:

```bash
uv pip install .
```

## Usage

### Basic Usage

To summarize all branches in the current git repository:

```bash
git-ai
```

### Specify a Branch

To summarize a specific branch:

```bash
git-ai --branch main
```

### Generate a Changelog

To generate a changelog file:

```bash
git-ai --changelog
```

By default, the changelog will be written to a file named `changelog_<branch>.md` in the current directory.

### Specify Output Directory

To specify an output directory for the changelog files:

```bash
git-ai --changelog --output ./docs
```

### Full Options

```
usage: git-ai [-h] [--branch BRANCH] [--changelog] [--output OUTPUT]

Git repository summarizer

optional arguments:
  -h, --help            show this help message and exit
  --branch BRANCH, -b BRANCH
                        Specify a branch (default: all branches)
  --changelog, -c       Generate a changelog file
  --output OUTPUT, -o OUTPUT
                        Output directory for changelog files (default: current
                        directory)
```

## Development

### Running Tests

To run the tests:

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=src
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.