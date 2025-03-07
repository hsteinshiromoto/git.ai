#!/usr/bin/env python3

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.git_summarizer import (
    summarize_changes,
    generate_summary,
)


def test_summarize_changes():
    # Test data
    test_commits = [
        {
            "hash": "abcdef",
            "author": "Test Author",
            "date": "2023-01-01",
            "message": "Test commit",
            "changes": [
                {"type": "A", "path": "file1.py"},
                {"type": "M", "path": "file2.py"},
                {"type": "D", "path": "file3.py"},
            ]
        },
        {
            "hash": "123456",
            "author": "Another Author",
            "date": "2023-01-02",
            "message": "Another commit",
            "changes": [
                {"type": "M", "path": "file1.py"},  # Modified after adding
                {"type": "A", "path": "file4.py"},
            ]
        }
    ]
    
    expected_summary = {
        "added": {"file1.py": 1, "file4.py": 1},
        "modified": {"file1.py": 1, "file2.py": 1},
        "deleted": {"file3.py": 1},
    }
    
    # Run the function
    result = summarize_changes(test_commits)
    
    # Check the result
    assert result == expected_summary


def test_generate_summary_empty():
    # Test with empty commits
    result = generate_summary("test-branch", [])
    assert result == "Branch 'test-branch': No commits found."