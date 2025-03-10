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
from modules.git_utils import run_git_command
from modules.tree import display_tree


def main():
    # Print ASCII art banner
    for line in GITGURU_BANNER.splitlines():
        print(f"{HEADING_COLOR}{line}{RESET_COLOR}")
        sys.stdout.flush()
        time.sleep(0.05)
    print(f"{HEADING_COLOR}Version: {VERSION}{RESET_COLOR}")

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

    # Set default git directory and command
    git_dir = "."
    command = "view" if len(sys.argv) == 1 else sys.argv[1]
    args = sys.argv[1:] if len(sys.argv) == 1 else sys.argv[2:]

    # Handle view command with optional directory
    if command == "view":
        if args and len(args) > 1:
            print(f"{HEADING_COLOR}Error: Invalid arguments for 'view'. Specify [git_dir] only.{RESET_COLOR}")
            sys.exit(1)
        if args:
            git_dir = args[0]
        if not os.path.isdir(os.path.join(git_dir, ".git")):
            print(f"{HEADING_COLOR}Error: '{git_dir}' is not a Git repository. Use 'init' to initialize one.{RESET_COLOR}")
            sys.exit(1)
        display_tree(git_dir)
        sys.exit(0)

    # Check if it's a Git repository for all other commands
    if not os.path.isdir(os.path.join(git_dir, ".git")):
        print(f"{HEADING_COLOR}Error: '{git_dir}' is not a Git repository. Use 'init' to initialize one.{RESET_COLOR}")
        sys.exit(1)

    # Handle remaining commands
    if command == "branch":
        display_tree(git_dir, "Before Command")
        if len(sys.argv) < 5 or len(sys.argv) > 6:
            print(f"{HEADING_COLOR}Error: 'branch' requires version, owner, type, and optional description.{RESET_COLOR}")
            sys.exit(1)
        version, owner, branch_type = sys.argv[2:5]
        description = sys.argv[5] if len(sys.argv) == 6 else None
        create_new_branch(version, owner, branch_type, description)

    elif command == "merge":
        display_tree(git_dir, "Before Command")
        if len(sys.argv) != 4:
            print(f"{HEADING_COLOR}Error: 'merge' requires source and target branches.{RESET_COLOR}")
            sys.exit(1)
        source, target = sys.argv[2:4]
        merge_branches(source, target)

    elif command == "commit":
        display_tree(git_dir, "Before Command")
        if len(sys.argv) < 3:
            print(f"{HEADING_COLOR}Error: 'commit' requires a message.{RESET_COLOR}")
            sys.exit(1)
        message = " ".join(sys.argv[2:])
        commit_changes(message)

    elif command == "push":
        display_tree(git_dir, "Before Command")
        if len(sys.argv) != 2:
            print(f"{HEADING_COLOR}Error: 'push' takes no arguments.{RESET_COLOR}")
            sys.exit(1)
        push_branch()

    elif command == "switch":
        display_tree(git_dir, "Before Command")
        if len(sys.argv) != 3:
            print(f"{HEADING_COLOR}Error: 'switch' requires a branch name.{RESET_COLOR}")
            sys.exit(1)
        branch = sys.argv[2]
        switch_branch(branch)

    elif command == "delete":
        display_tree(git_dir, "Before Command")
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

    elif command == "cto-hotfix":
        display_tree(git_dir, "Before CTO Hotfix")
        if len(sys.argv) != 3:
            print(f"{HEADING_COLOR}Error: 'cto-hotfix' requires version only (e.g., 'cto-hotfix 0.0.2').{RESET_COLOR}")
            sys.exit(1)
        version = sys.argv[2]
        # Switch to main first, then create the hotfix branch without description
        switch_branch("main")
        create_new_branch(version, "cto", "hotfix", None)

    elif command == "cto-hotfix-push":
        display_tree(git_dir, "Before CTO Hotfix Push")
        if len(sys.argv) != 3:
            print(f"{HEADING_COLOR}Error: 'cto-hotfix-push' requires the hotfix version (e.g., 'cto-hotfix-push 0.0.2').{RESET_COLOR}")
            sys.exit(1)
        version = sys.argv[2]
        hotfix_branch = f"{version}/cto/hotfix"
        # Check if the branch exists
        branches = run_git_command(["git", "branch"], "Failed to list branches").strip().splitlines()
        if not any(b.strip().strip('* ') == hotfix_branch for b in branches):
            print(f"{HEADING_COLOR}Error: Hotfix branch '{hotfix_branch}' does not exist. Create it first with 'cto-hotfix'.{RESET_COLOR}")
            sys.exit(1)
        # Switch to main, merge the hotfix, and push
        switch_branch("main")
        merge_branches(hotfix_branch, "main")
        push_branch()
        # Optionally delete the hotfix branch after merging
        delete_branches([hotfix_branch], force=False)

    else:
        print(f"{HEADING_COLOR}Error: Unknown command '{command}'. Try 'help' for available commands.{RESET_COLOR}")
        sys.exit(1)


if __name__ == "__main__":
    main()
