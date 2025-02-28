import os
import sys
import threading
from .constants import HEADING_COLOR, CONTENT_COLOR, RESET_COLOR, VALID_TYPES, BRANCH_PATTERN
from .git_utils import run_git_command
from .ui import animate_loading
from .tree import display_tree

def validate_branch_name(branch):
    """Check if branch name follows the convention."""
    if not BRANCH_PATTERN.match(branch):
        print(f"{HEADING_COLOR}Error: Invalid branch name '{branch}'. Must be 'main' or follow <version>/<owner>/<type>[/<description>] (e.g., 0.0.1/tom/feature/test).{RESET_COLOR}")
        sys.exit(1)

def init_git_repo(git_dir="."):
    """Initialize a new Git repository with an initial commit on main, staging all existing files."""
    os.chdir(git_dir)
    
    stop_event = threading.Event()
    animation_thread = threading.Thread(target=animate_loading, args=(stop_event, f"Initializing Git repository in {git_dir}"))
    animation_thread.start()

    if os.path.isdir(".git"):
        stop_event.set()
        animation_thread.join()
        print(f"{HEADING_COLOR}Error: Directory '{git_dir}' is already a Git repository.{RESET_COLOR}")
        sys.exit(1)

    run_git_command(["git", "init"], "Failed to initialize Git repository")
    run_git_command(["git", "add", "."], "Failed to stage existing files")
    run_git_command(["git", "commit", "-m", "Initial commit with existing files"], "Failed to create initial commit")
    
    current_branch = run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], "Failed to get current branch").strip()
    if current_branch != "main":
        run_git_command(["git", "branch", "-m", current_branch, "main"], "Failed to rename branch to 'main'")

    stop_event.set()
    animation_thread.join()
    print(f"{CONTENT_COLOR}Git repository initialized successfully with 'main' branch in '{git_dir}', including all existing files.{RESET_COLOR}")
    display_tree(git_dir, "After Initialization")

def create_new_branch(version, owner, branch_type, description=None):
    """Create a new branch, requiring base release branch to exist."""
    if branch_type not in VALID_TYPES:
        print(f"{HEADING_COLOR}Error: Invalid type '{branch_type}'. Must be one of: feature, bugfix, hotfix, release.{RESET_COLOR}")
        sys.exit(1)
    if not re.match(r'^\d+\.\d+(?:\.\d+)?$', version):
        print(f"{HEADING_COLOR}Error: Version '{version}' must be in X.Y or X.Y.Z format.{RESET_COLOR}")
        sys.exit(1)
    if not re.match(r'^[a-z]+$', owner):
        print(f"{HEADING_COLOR}Error: Owner '{owner}' must be lowercase letters only.{RESET_COLOR}")
        sys.exit(1)
    if description and not re.match(r'^[a-z0-9-]+$', description):
        print(f"{HEADING_COLOR}Error: Description '{description}' must be lowercase letters, numbers, or hyphens.{RESET_COLOR}")
        sys.exit(1)

    branch = f"{version}/{owner}/{branch_type}" + (f"/{description}" if description else "")
    base_branch = "main" if branch_type == "release" else f"{version}/{owner}/release"
    
    stop_event = threading.Event()
    animation_thread = threading.Thread(target=animate_loading, args=(stop_event, f"Creating branch {branch}"))
    animation_thread.start()

    branches = run_git_command(["git", "branch"], "Failed to list branches").strip().splitlines()
    base_exists = any(b.strip().strip('* ') == base_branch for b in branches)
    if not base_exists:
        stop_event.set()
        animation_thread.join()
        print(f"{HEADING_COLOR}Error: Base branch '{base_branch}' does not exist. Create it first with 'new {version} {owner} release'.{RESET_COLOR}")
        sys.exit(1)

    run_git_command(["git", "checkout", base_branch], f"Failed to checkout {base_branch}")
    run_git_command(["git", "checkout", "-b", branch], f"Failed to create branch {branch}")

    stop_event.set()
    animation_thread.join()
    print(f"{CONTENT_COLOR}Branch '{branch}' created successfully.{RESET_COLOR}")
    current_branch = run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], "Failed to get current branch").strip()
    print(f"{CONTENT_COLOR}Current branch: {current_branch}{RESET_COLOR}")
    display_tree(".", "After Branch Creation")

def merge_branches(source, target):
    """Merge source branch into target with validation, auto-committing changes before merge."""
    validate_branch_name(source)
    validate_branch_name(target)
    
    stop_event = threading.Event()
    animation_thread = threading.Thread(target=animate_loading, args=(stop_event, f"Merging {source} into {target}"))
    animation_thread.start()

    run_git_command(["git", "checkout", target], f"Failed to checkout {target}")
    status_output = subprocess.run(["git", "status", "--porcelain"], text=True, capture_output=True).stdout
    if status_output.strip():
        run_git_command(["git", "add", "."], "Failed to stage changes before merge")
        run_git_command(["git", "commit", "-m", "Commit before merge"], "Failed to commit changes before merge")
        print(f"{CONTENT_COLOR}Staged and committed changes on '{target}' before merge.{RESET_COLOR}")

    run_git_command(["git", "merge", "--no-ff", source, "-m", f"Merge {source} into {target}"], f"Failed to merge {source} into {target}")

    stop_event.set()
    animation_thread.join()
    print(f"{CONTENT_COLOR}Merged '{source}' into '{target}' successfully.{RESET_COLOR}")
    display_tree(".", "After Merge")

def commit_changes(message):
    """Commit changes with a message."""
    stop_event = threading.Event()
    animation_thread = threading.Thread(target=animate_loading, args=(stop_event, "Committing changes"))
    animation_thread.start()

    run_git_command(["git", "add", "."], "Failed to stage changes")
    run_git_command(["git", "commit", "-m", message], "Failed to commit changes")

    stop_event.set()
    animation_thread.join()
    print(f"{CONTENT_COLOR}Changes committed with message '{message}'.{RESET_COLOR}")
    display_tree(".", "After Commit")

def push_branch():
    """Push the current branch to origin."""
    current_branch = run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], "Failed to get current branch").strip()
    validate_branch_name(current_branch)
    
    stop_event = threading.Event()
    animation_thread = threading.Thread(target=animate_loading, args=(stop_event, f"Pushing {current_branch} to origin"))
    animation_thread.start()

    run_git_command(["git", "push", "origin", current_branch], f"Failed to push {current_branch}")

    stop_event.set()
    animation_thread.join()
    print(f"{CONTENT_COLOR}Pushed '{current_branch}' to origin successfully.{RESET_COLOR}")
    display_tree(".", "After Push")

def switch_branch(branch):
    """Switch to an existing branch."""
    validate_branch_name(branch)
    
    stop_event = threading.Event()
    animation_thread = threading.Thread(target=animate_loading, args=(stop_event, f"Switching to {branch}"))
    animation_thread.start()

    run_git_command(["git", "checkout", branch], f"Failed to switch to {branch}")

    stop_event.set()
    animation_thread.join()
    print(f"{CONTENT_COLOR}Switched to '{branch}' successfully.{RESET_COLOR}")
    display_tree(".", "After Switch")

def delete_branches(branches_to_delete, force=False):
    """Delete multiple branches with optional force flag."""
    current_branch = run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], "Failed to get current branch").strip()
    existing_branches = run_git_command(["git", "branch"], "Failed to list branches").strip().splitlines()
    existing_branches = [b.strip().strip('* ') for b in existing_branches]

    stop_event = threading.Event()
    animation_thread = threading.Thread(target=animate_loading, args=(stop_event, f"Deleting branches"))
    animation_thread.start()

    deleted_count = 0
    for branch in branches_to_delete:
        validate_branch_name(branch)
        if branch == current_branch:
            print(f"{HEADING_COLOR}Error: Cannot delete the current branch '{branch}'. Switch to another branch first.{RESET_COLOR}")
            continue
        if branch not in existing_branches:
            print(f"{HEADING_COLOR}Error: Branch '{branch}' does not exist.{RESET_COLOR}")
            continue
        
        delete_cmd = ["git", "branch", "-D" if force else "-d", branch]
        try:
            run_git_command(delete_cmd, f"Failed to delete branch {branch}")
            print(f"{CONTENT_COLOR}Branch '{branch}' deleted successfully.{RESET_COLOR}")
            deleted_count += 1
        except SystemExit:
            continue

    stop_event.set()
    animation_thread.join()
    if deleted_count > 0:
        print(f"{CONTENT_COLOR}Deleted {deleted_count} branch(es) successfully.{RESET_COLOR}")
    else:
        print(f"{CONTENT_COLOR}No branches were deleted.{RESET_COLOR}")
    display_tree(".", "After Deletion")
