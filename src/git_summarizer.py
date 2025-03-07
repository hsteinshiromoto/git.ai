#!/usr/bin/env python3

import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple


def run_git_command(command: List[str]) -> str:
    """Run a git command and return its output.

    This function executes a git command using subprocess and returns the command output.
    It handles errors by printing the error message and exiting.

    Args:
        command: A list of strings representing the git command and its arguments.
            Example: ["log", "--oneline", "-n", "5"]

    Returns:
        The standard output of the command as a string, with trailing whitespace removed.

    Raises:
        SystemExit: If the git command fails.

    Examples:
        >>> # This doctest is skipped as it depends on git repo state
        >>> # run_git_command(["status", "--porcelain"])
        >>> # ''
    """
    try:
        result = subprocess.run(
            ["git"] + command,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}", file=sys.stderr)
        print(f"Error details: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def get_branches() -> List[str]:
    """Get a list of all git branches in the current repository.

    This function retrieves all local branches from the git repository
    using the git branch command.

    Returns:
        A list of branch names as strings.

    Examples:
        >>> # This doctest is skipped as it depends on git repo state
        >>> # branches = get_branches()
        >>> # 'main' in branches
        >>> # True
    """
    output = run_git_command(["branch", "--format=%(refname:short)"])
    return [branch for branch in output.split("\n") if branch]


def get_commit_history(branch: str) -> List[Dict]:
    """Get detailed commit history for a specified branch.

    This function retrieves the commit history for a given branch including
    hash, author, date, commit message, and file changes for each commit.

    Args:
        branch: The name of the git branch to retrieve history for.

    Returns:
        A list of dictionaries, each representing a commit with the following keys:
        - hash: The full commit hash
        - author: The author's name
        - date: The commit date in YYYY-MM-DD format
        - message: The commit message
        - changes: A list of dictionaries with 'type' and 'path' keys representing file changes

    Examples:
        >>> # This doctest is skipped as it depends on git repo state
        >>> # commits = get_commit_history('main')
        >>> # commit = commits[0] if commits else {}
        >>> # sorted(list(commit.keys()) if commit else [])
        >>> # ['author', 'changes', 'date', 'hash', 'message']
    """
    # Format: hash, author name, date, subject, files changed
    format_str = "%H|%an|%ad|%s|"

    output = run_git_command(
        [
            "log",
            branch,
            f"--pretty=format:{format_str}",
            "--date=short",
            "--name-status",
        ]
    )

    commits = []
    current_commit = None

    for line in output.split("\n"):
        if not line.strip():
            continue

        # If the line contains our delimiter, it's a new commit
        if "|" in line:
            if current_commit:
                commits.append(current_commit)

            parts = line.split("|")
            if len(parts) >= 4:
                current_commit = {
                    "hash": parts[0],
                    "author": parts[1],
                    "date": parts[2],
                    "message": parts[3],
                    "changes": [],
                }
        elif current_commit:
            # This is a file change line
            parts = line.split("\t")
            if len(parts) >= 2:
                change_type = parts[0]
                file_path = parts[1]
                current_commit["changes"].append(
                    {"type": change_type, "path": file_path}
                )

    # Add the last commit
    if current_commit:
        commits.append(current_commit)

    return commits


def summarize_changes(commits: List[Dict]) -> Dict[str, Dict]:
    """Categorize and count file changes across multiple commits.

    This function analyzes a list of commits and categorizes file changes as
    added, modified, or deleted, counting how many times each file appears
    in each category.

    Args:
        commits: A list of commit dictionaries, each containing a 'changes' key
                with a list of file changes.

    Returns:
        A dictionary with three keys ('added', 'modified', 'deleted'), each
        containing a sub-dictionary mapping file paths to the number of times
        they appear in commits within that category.

    Examples:
        >>> # Create sample test data
        >>> sample_commits = [
        ...     {'changes': [
        ...         {'type': 'A', 'path': 'file1.txt'},
        ...         {'type': 'M', 'path': 'file2.txt'}
        ...     ]},
        ...     {'changes': [
        ...         {'type': 'M', 'path': 'file2.txt'},
        ...         {'type': 'D', 'path': 'file3.txt'}
        ...     ]}
        ... ]
        >>> summary = summarize_changes(sample_commits)
        >>> summary['added']
        {'file1.txt': 1}
        >>> summary['modified']
        {'file2.txt': 2}
        >>> summary['deleted']
        {'file3.txt': 1}
    """
    summary = {
        "added": {},
        "modified": {},
        "deleted": {},
    }

    for commit in commits:
        for change in commit["changes"]:
            change_type = change["type"]
            file_path = change["path"]

            # Map git status to our categories
            if change_type == "A":  # Added
                category = "added"
            elif change_type in ["M", "R"]:  # Modified or Renamed
                category = "modified"
            elif change_type == "D":  # Deleted
                category = "deleted"
            else:
                continue  # Skip other types

            # Count occurrences of each file
            if file_path not in summary[category]:
                summary[category][file_path] = 0
            summary[category][file_path] += 1

    return summary


def generate_summary(branch_name: str, commits: List[Dict]) -> str:
    """Generate a human-readable text summary of branch activity.

    This function creates a formatted text summary of all the file changes
    in a branch, grouped by category (added, modified, deleted).

    Args:
        branch_name: The name of the git branch being summarized.
        commits: A list of commit dictionaries from the branch.

    Returns:
        A formatted string containing the branch summary.

    Examples:
        >>> empty_summary = generate_summary('test-branch', [])
        >>> empty_summary
        "Branch 'test-branch': No commits found."

        >>> # Create sample test data
        >>> sample_commits = [
        ...     {'changes': [
        ...         {'type': 'A', 'path': 'file1.txt'},
        ...         {'type': 'M', 'path': 'file2.txt'}
        ...     ]},
        ...     {'changes': [
        ...         {'type': 'M', 'path': 'file2.txt'},
        ...         {'type': 'D', 'path': 'file3.txt'}
        ...     ]}
        ... ]
        >>> summary = generate_summary('feature', sample_commits)
        >>> "Branch 'feature': 2 commits" in summary
        True
        >>> "Added files:" in summary
        True
        >>> "file1.txt (in 1 commits)" in summary
        True
        >>> "file2.txt (in 2 commits)" in summary
        True
    """
    if not commits:
        return f"Branch '{branch_name}': No commits found."

    changes = summarize_changes(commits)

    summary = [f"Branch '{branch_name}': {len(commits)} commits"]

    # Add added files
    if changes["added"]:
        summary.append("\nAdded files:")
        for file_path, count in sorted(changes["added"].items()):
            summary.append(f"  - {file_path} (in {count} commits)")

    # Add modified files
    if changes["modified"]:
        summary.append("\nModified files:")
        for file_path, count in sorted(changes["modified"].items()):
            summary.append(f"  - {file_path} (in {count} commits)")

    # Add deleted files
    if changes["deleted"]:
        summary.append("\nDeleted files:")
        for file_path, count in sorted(changes["deleted"].items()):
            summary.append(f"  - {file_path} (in {count} commits)")

    return "\n".join(summary)


def generate_changelog(branch_name: str, commits: List[Dict], output_file: str) -> None:
    """Generate a formatted changelog markdown file for a branch.

    This function creates a markdown file with all commits in the branch,
    organized by date in reverse chronological order. Each commit includes
    the commit message, author, hash, and details about file changes.

    Args:
        branch_name: The name of the git branch to generate a changelog for.
        commits: A list of commit dictionaries from the branch.
        output_file: The path where the changelog file should be written.

    Returns:
        None

    Examples:
        >>> import tempfile
        >>> import os
        >>> # Create sample test data
        >>> sample_commits = [
        ...     {
        ...         'hash': '1234567890abcdef1234567890abcdef12345678',
        ...         'author': 'Test User',
        ...         'date': '2023-01-01',
        ...         'message': 'Initial commit',
        ...         'changes': [
        ...             {'type': 'A', 'path': 'file1.txt'},
        ...             {'type': 'A', 'path': 'file2.txt'}
        ...         ]
        ...     }
        ... ]
        >>> # Use a temporary file for testing
        >>> with tempfile.NamedTemporaryFile(delete=False) as temp:
        ...     temp_path = temp.name
        >>> # Generate the changelog
        >>> generate_changelog('test', sample_commits, temp_path)
        >>> # Check if file exists and has content
        >>> os.path.exists(temp_path)
        True
        >>> with open(temp_path, 'r') as f:
        ...     content = f.read()
        >>> '# Changelog for test' in content
        True
        >>> '## 2023-01-01' in content
        True
        >>> 'Initial commit (Test User, 1234567)' in content
        True
        >>> os.unlink(temp_path)  # Clean up the temporary file
    """
    with open(output_file, "w") as f:
        f.write(f"# Changelog for {branch_name}\n\n")

        # Group commits by date
        commits_by_date = defaultdict(list)
        for commit in commits:
            commits_by_date[commit["date"]].append(commit)

        # Write commits grouped by date
        for date in sorted(commits_by_date.keys(), reverse=True):
            f.write(f"## {date}\n\n")

            for commit in commits_by_date[date]:
                author = commit["author"]
                message = commit["message"]
                commit_hash = commit["hash"][:7]  # Short hash

                f.write(f"- {message} ({author}, {commit_hash})\n")

                # Add details about file changes
                added = []
                modified = []
                deleted = []

                for change in commit["changes"]:
                    if change["type"] == "A":
                        added.append(change["path"])
                    elif change["type"] in ["M", "R"]:
                        modified.append(change["path"])
                    elif change["type"] == "D":
                        deleted.append(change["path"])

                if added:
                    f.write(f"  - Added: {', '.join(added)}\n")
                if modified:
                    f.write(f"  - Modified: {', '.join(modified)}\n")
                if deleted:
                    f.write(f"  - Deleted: {', '.join(deleted)}\n")

                f.write("\n")

            f.write("\n")


def main() -> None:
    """Main function that parses command line arguments and processes git branches.

    This function serves as the entry point for the git summarizer tool.
    It parses command line arguments, determines which branches to process,
    generates summaries for each branch, and optionally creates changelog files.

    Returns:
        None

    Examples:
        >>> # This doctest is skipped as it requires command line arguments
        >>> # and interacts with git
        >>> # main()
    """
    parser = argparse.ArgumentParser(description="Git repository summarizer")
    parser.add_argument(
        "--branch", "-b", help="Specify a branch (default: all branches)", default=None
    )
    parser.add_argument(
        "--changelog", "-c", help="Generate a changelog file", action="store_true"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output directory for changelog files (default: current directory)",
        default=".",
    )

    args = parser.parse_args()

    # Determine which branches to process
    if args.branch:
        branches = [args.branch]
    else:
        branches = get_branches()

    # Process each branch
    for branch in branches:
        commits = get_commit_history(branch)
        summary = generate_summary(branch, commits)
        print(summary)
        print("\n" + "-" * 50 + "\n")

        # Generate changelog if requested
        if args.changelog:
            output_file = os.path.join(args.output, f"changelog_{branch}.md")
            generate_changelog(branch, commits, output_file)
            print(f"Changelog generated: {output_file}")


if __name__ == "__main__":
    main()
