import sys
import threading
import time
from .constants import HEADING_COLOR, CONTENT_COLOR, RESET_COLOR


def animate_loading(stop_event, message="Processing Git command"):
    """Display a Braille spinner animation until stopped."""
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    idx = 0
    while not stop_event.is_set():
        sys.stdout.write(f"\r{CONTENT_COLOR}{message} {spinner[idx]}{RESET_COLOR}")
        sys.stdout.flush()
        idx = (idx + 1) % len(spinner)
        time.sleep(0.1)
    sys.stdout.write(f"\r{CONTENT_COLOR}{message} Done!{RESET_COLOR}\n")
    sys.stdout.flush()


def display_commands(script_path):
    """Display available commands."""
    print(f"{HEADING_COLOR}Available Commands:{RESET_COLOR}")
    print(f"{CONTENT_COLOR}  init [git_dir]                             Initialize a new Git repository (defaults to PWD if git_dir omitted){RESET_COLOR}")
    print(f"{CONTENT_COLOR}  view [git_dir]                             Visualize branch tree (defaults to PWD if git_dir omitted){RESET_COLOR}")
    print(f"{CONTENT_COLOR}  new <version> <owner> <type> [desc]        Create a new branch (type must be: feature, bugfix, hotfix, release){RESET_COLOR}")
    print(f"{CONTENT_COLOR}  merge <source> <target>                    Merge source into target (auto-commits changes before merge){RESET_COLOR}")
    print(f"{CONTENT_COLOR}  commit <message>                           Commit changes{RESET_COLOR}")
    print(f"{CONTENT_COLOR}  push                                       Push current branch to origin{RESET_COLOR}")
    print(f"{CONTENT_COLOR}  switch <branch>                            Switch to a branch{RESET_COLOR}")
    print(f"{CONTENT_COLOR}  delete <branch1> [branch2] ... [--force]   Delete one or more branches (use --force for unmerged branches){RESET_COLOR}")
    print(f"{CONTENT_COLOR}  cto-hotfix <version>                       Quickly get the CTO working on a hotfix branch{RESET_COLOR}")
    print(f"{CONTENT_COLOR}  cto-hotfix-push <version>                  Merge and push the hotfix to main{RESET_COLOR}")
    print(f"{HEADING_COLOR}Examples:{RESET_COLOR}")
    print(f"{CONTENT_COLOR}  {script_path} init /path/to/repo{RESET_COLOR}")
    print(f"{CONTENT_COLOR}  {script_path} view /path/to/repo{RESET_COLOR}")
    print(f"{CONTENT_COLOR}  {script_path} new 0.0.1 tom feature test-feature{RESET_COLOR}")
    print(f"{CONTENT_COLOR}  {script_path} merge 0.0.1/tom/feature/test-feature 0.0.1/tom/release{RESET_COLOR}")
