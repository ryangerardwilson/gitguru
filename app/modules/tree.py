import threading
from collections import defaultdict
from datetime import datetime
import re
from .constants import HEADING_COLOR, CONTENT_COLOR, RESET_COLOR
from .git_utils import run_git_command, get_git_branches
from .ui import animate_loading


def build_branch_tree(branches, current_branch, log_lines):
    """Return the raw git log --graph --oneline --all --decorate output."""
    return log_lines


def display_tree(git_dir=".", label=None):
    """Display the Git branch tree with a custom label."""
    stop_event = threading.Event()
    animation_thread = threading.Thread(target=animate_loading, args=(stop_event, "Fetching branches"))
    animation_thread.start()
    branches, current_branch, log_lines = get_git_branches(git_dir)
    tree_lines = build_branch_tree(branches, current_branch, log_lines)
    stop_event.set()
    animation_thread.join()

    if label:
        print(f"\n{HEADING_COLOR}Git Branch Tree ({label}):{RESET_COLOR}")
    else:
        print(f"\n{HEADING_COLOR}Git Branch Tree:{RESET_COLOR}")

    for line in tree_lines:
        print(f"{CONTENT_COLOR}{line}{RESET_COLOR}")
    print(f"\n{HEADING_COLOR}{'=' * 50}{RESET_COLOR}")
    print(f"{CONTENT_COLOR}Current branch: {current_branch}{RESET_COLOR}")
