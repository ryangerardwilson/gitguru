#!/usr/bin/env python3
import sys
import os
import time
from modules.constants import GITGURU_BANNER, HEADING_COLOR, CONTENT_COLOR, RESET_COLOR, VERSION
from modules.ui import display_commands
from modules.branch_ops import (
    init_git_repo, create_new_branch, merge_branches, commit_changes,
    push_branch, switch_branch, delete_branches
)
from modules.tree import display_tree

def main():
    # Print ASCII art banner
    for line in GITGURU_BANNER.splitlines():
        print(f"{HEADING_COLOR}{line}{RESET_COLOR}")
        sys.stdout.flush()
        time.sleep(0.05)
    print(f"{HEADING_COLOR}Version: {VERSION}{RESET_COLOR}")  # Print version after banner

    # Handle help and init commands
    script_path = os.path.realpath(sys.argv[0])
    if len(sys.argv) > 1 and sys.argv[1] == "help":
        git_dir = "."
        if os.path.isdir(os.path.join(git_dir, ".git")):
            display_tree(git_dir, "Before Help")
        display_commands(script_path)
        sys.exit(0)
    elif len(sys.argv) > 1 and sys.argv[1] == "init":
        git_dir = sys.argv[2] if len(sys.argv) > 2 else "."
        if len(sys.argv) > 3:
            print(f"{HEADING_COLOR}Error: 'init' accepts only an optional [git_dir].{RESET_COLOR}")
            sys.exit(1)
        init_git_repo(git_dir)
        sys.exit(0)

    # Rest of the main function remains unchanged
    git_dir = "."
    command = "view" if len(sys.argv) == 1 else sys.argv[1]
    args = sys.argv[1:] if len(sys.argv) == 1 else sys.argv[2:]
    if command == "view" and args and len(args) > 1:
        print(f"{HEADING_COLOR}Error: Invalid arguments for 'view'. Specify [git_dir] only.{RESET_COLOR}")
        sys.exit(1)
    if command == "view" and args:
        git_dir = args[0]
    if os.path.isdir(os.path.join(git_dir, ".git")):
        display_tree(git_dir, "Before Command")
    else:
        print(f"{HEADING_COLOR}Error: '{git_dir}' is not a Git repository. Use 'init' to initialize one.{RESET_COLOR}")
        sys.exit(1)

    if command == "view":
        if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == "view"):
            print(f"{CONTENT_COLOR}Add 'help' to see available commands.{RESET_COLOR}")
            print(f"{HEADING_COLOR}{'=' * 50}{RESET_COLOR}")
        sys.exit(0)

    elif command == "new":
        if len(sys.argv) < 5 or len(sys.argv) > 6:
            print(f"{HEADING_COLOR}Error: 'new' requires version, owner, type, and optional description.{RESET_COLOR}")
            sys.exit(1)
        version, owner, branch_type = sys.argv[2:5]
        description = sys.argv[5] if len(sys.argv) == 6 else None
        create_new_branch(version, owner, branch_type, description)

    elif command == "merge":
        if len(sys.argv) != 4:
            print(f"{HEADING_COLOR}Error: 'merge' requires source and target branches.{RESET_COLOR}")
            sys.exit(1)
        source, target = sys.argv[2:4]
        merge_branches(source, target)

    elif command == "commit":
        if len(sys.argv) < 3:
            print(f"{HEADING_COLOR}Error: 'commit' requires a message.{RESET_COLOR}")
            sys.exit(1)
        message = " ".join(sys.argv[2:])
        commit_changes(message)

    elif command == "push":
        if len(sys.argv) != 2:
            print(f"{HEADING_COLOR}Error: 'push' takes no arguments.{RESET_COLOR}")
            sys.exit(1)
        push_branch()

    elif command == "switch":
        if len(sys.argv) != 3:
            print(f"{HEADING_COLOR}Error: 'switch' requires a branch name.{RESET_COLOR}")
            sys.exit(1)
        branch = sys.argv[2]
        switch_branch(branch)

    elif command == "delete":
        if len(sys.argv) < 3:
            print(f"{HEADING_COLOR}Error: 'delete' requires at least one branch name.{RESET_COLOR}")
            sys.exit(1)
        args = sys.argv[2:]
        force = "--force" in args
        branches_to_delete = [arg for arg in args if arg != "--force"]
        if not branches_to_delete:
            print(f"{HEADING_COLOR}Error: No branches specified to delete.{RESET_COLOR}")
            sys.exit(1)
        delete_branches(branches_to_delete, force)

    else:
        print(f"{HEADING_COLOR}Error: Unknown command '{command}'. Try 'help' for available commands.{RESET_COLOR}")
        sys.exit(1)

if __name__ == "__main__":
    main()
