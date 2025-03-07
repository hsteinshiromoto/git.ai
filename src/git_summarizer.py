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
    """Run a git command and return its output."""
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
    """Get list of all git branches."""
    output = run_git_command(["branch", "--format=%(refname:short)"])
    return [branch for branch in output.split('\n') if branch]


def get_commit_history(branch: str) -> List[Dict]:
    """Get commit history for a branch."""
    # Format: hash, author name, date, subject, files changed
    format_str = "%H|%an|%ad|%s|"
    
    output = run_git_command([
        "log", 
        branch, 
        f"--pretty=format:{format_str}", 
        "--date=short", 
        "--name-status"
    ])
    
    commits = []
    current_commit = None
    
    for line in output.split('\n'):
        if not line.strip():
            continue
        
        # If the line contains our delimiter, it's a new commit
        if "|" in line:
            if current_commit:
                commits.append(current_commit)
            
            parts = line.split('|')
            if len(parts) >= 4:
                current_commit = {
                    "hash": parts[0],
                    "author": parts[1],
                    "date": parts[2],
                    "message": parts[3],
                    "changes": []
                }
        elif current_commit:
            # This is a file change line
            parts = line.split('\t')
            if len(parts) >= 2:
                change_type = parts[0]
                file_path = parts[1]
                current_commit["changes"].append({
                    "type": change_type,
                    "path": file_path
                })
    
    # Add the last commit
    if current_commit:
        commits.append(current_commit)
    
    return commits


def summarize_changes(commits: List[Dict]) -> Dict[str, Dict]:
    """Summarize all changes across commits."""
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
    """Generate a text summary for a branch."""
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
    """Generate a changelog file for a branch."""
    with open(output_file, 'w') as f:
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


def main():
    parser = argparse.ArgumentParser(description="Git repository summarizer")
    parser.add_argument(
        "--branch", "-b", 
        help="Specify a branch (default: all branches)",
        default=None
    )
    parser.add_argument(
        "--changelog", "-c",
        help="Generate a changelog file",
        action="store_true"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output directory for changelog files (default: current directory)",
        default="."
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