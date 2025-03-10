import subprocess
import sys
from .constants import HEADING_COLOR, RESET_COLOR


def run_git_command(cmd, error_message="Git command failed"):
    """Execute a Git command and handle errors."""
    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"{HEADING_COLOR}Error: {error_message}: {e.stderr}{RESET_COLOR}")
        sys.exit(1)


def get_git_branches(git_dir="."):
    """Fetch Git branch and commit data using git log --graph --oneline --all --decorate."""
    import os
    os.chdir(git_dir)
    run_git_command(["git", "rev-parse", "--is-inside-work-tree"], "Not a Git repository")
    branches_output = run_git_command(["git", "branch"], "Failed to fetch branches").strip().splitlines()

    branches = []
    current_branch = None
    for line in branches_output:
        line = line.strip()
        if line.startswith('*'):
            current_branch = line[2:]
            branches.append(current_branch)
        else:
            branch = line[2:] if line.startswith('  ') else line
            branches.append(branch)

    log_output = run_git_command(
        ["git", "log", "--graph", "--oneline", "--all", "--decorate"],
        "Failed to fetch log"
    ).strip().splitlines()

    return branches, current_branch, log_output
