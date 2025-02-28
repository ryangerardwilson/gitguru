import threading
from collections import defaultdict
from datetime import datetime
import re
from .constants import HEADING_COLOR, CONTENT_COLOR, RESET_COLOR
from .git_utils import run_git_command, get_git_branches
from .ui import animate_loading

def build_branch_tree(branches, current_branch, log_lines):
    """Build a nested ASCII art representation of the branch tree with commit history."""
    tree_lines = []
    
    branch_heads = {}
    for branch in branches:
        head_commit = run_git_command(
            ["git", "rev-parse", "--short", branch], 
            f"Failed to get HEAD of {branch}"
        ).strip()
        branch_heads[branch] = head_commit
    
    current_branch_head = branch_heads[current_branch]
    
    for line in log_lines:
        if not line.strip() or not any(c.isalnum() for c in line.split()):
            tree_lines.append(line)
            continue

        match = re.search(r'([0-9a-f]{7,})\s+(.+)', line)
        if not match:
            tree_lines.append(line)
            continue
        
        commit_hash = match.group(1)
        message = match.group(2)
        timestamp = run_git_command(
            ["git", "log", "-1", "--format=%ct", commit_hash], "Failed to fetch timestamp"
        ).strip()
        ts = datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M') if timestamp else "Unknown"
        
        # Preserve graph characters but normalize spacing
        graph = line[:line.index(commit_hash)].rstrip()  # Remove trailing spaces
        tree_lines.append(f"{graph} {commit_hash} [{ts}] {message}")  # Single space after graph
        
        branches_here = [branch for branch, head in branch_heads.items() if head == commit_hash]
        if branches_here:
            def branch_sort_key(branch):
                if branch == "main":
                    return (2, "", "", branch)
                parts = branch.split('/')
                version_owner = f"{parts[0]}/{parts[1]}"
                branch_type = parts[2]
                is_release = 1 if branch_type == "release" else 0
                return (0, version_owner, is_release, branch)
            
            sorted_branches = sorted(branches_here, key=branch_sort_key)
            for i, branch in enumerate(sorted_branches):
                prefix = "└──" if i == len(sorted_branches) - 1 else "├──"
                branch_indicator = " *" if (branch == current_branch and commit_hash == current_branch_head) else ""
                tree_lines.append(f"    {prefix} {branch}{branch_indicator}")

    return tree_lines

def display_tree(git_dir=".", label="Current State"):
    """Display the Git branch tree with a custom label."""
    # print(f"{HEADING_COLOR}Visualizing Git branches for {git_dir} ({label})...{RESET_COLOR}")
    stop_event = threading.Event()
    animation_thread = threading.Thread(target=animate_loading, args=(stop_event, "Fetching branches"))
    animation_thread.start()
    branches, current_branch, log_lines = get_git_branches(git_dir)
    tree_lines = build_branch_tree(branches, current_branch, log_lines)
    stop_event.set()
    animation_thread.join()

    print(f"\n{HEADING_COLOR}Git Branch Tree ({label}):{RESET_COLOR}")
    for line in tree_lines:
        print(f"{CONTENT_COLOR}{line}{RESET_COLOR}")
    print(f"\n{HEADING_COLOR}{'=' * 50}{RESET_COLOR}")
    print(f"{CONTENT_COLOR}Current branch: {current_branch}{RESET_COLOR}")
