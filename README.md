# GitGuru

GitGuru is a command-line tool for managing Git branches with a structured naming convention. It simplifies branch creation, merging, committing, pushing, switching, and deletion, while providing a visual tree of your repository's branch structure. Visually, it emphasizes where each branch currently points (rather than its entire history), listing main only at d644eac reflects its HEAD position, avoiding redundancy.

## 1. Core Philosophy & Why This Works

GitGuru is a git collaboration workflow emphasizing simplicity and team-driven control over the development process. Here’s the core approach:

- **Block all pushes to `main`**: Use repository settings (e.g., GitHub branch protection) to prevent direct pushes to `main`. This ensures `main` remains a stable, production-ready branch.
- **Work in feature branches**: Team members develop on individual branches (e.g., `0.0.1/tom/feature/user-auth`), keeping work isolated and focused.
- **Merge into a release branch as a team**: Integrate all changes into a shared release branch (e.g., `0.0.1/team/release`) collaboratively. This allows the team to resolve conflicts together (e.g., Tom and Jane fixing overlaps in `main.py`) before anything reaches `main`.
- **Finalize by merging release into `main`**: Once the release branch is tested and stable, merge it into `main` as a single, deliberate step.

This, just works. Because:

- **Control**: No one can accidentally disrupt `main`—the remote enforces this, not just team discipline.
- **Team Sorting**: Merging into `release` as a team lets you tackle conflicts head-on, leveraging collective knowledge (e.g., fixing overlapping changes in real-time).
- **Simplicity**: Skip extra steps like pull requests—just use GitGuru’s commands (`gitguru merge`, `gitguru push`) and team agreement to get work done.

This philosophy trusts the team to self-organize and prioritizes direct collaboration over formalized review processes, making it ideal for tight-knit groups comfortable with Git and GitGuru’s workflow.

## 2. Installation / Upgrade to Latest Version

To install or upgrade to the latest version, run:

    bash -c "sh <(curl -fsSL https://files.ryangerardwilson.com/gitguru/install.sh)"

## 3. Subsequent Updates

To update your installation:

    sudo apt update
    sudo apt install --only-upgrade gitguru

## 4. Usage

GitGuru enforces a branch naming convention—`<version>/<owner>/<type>[/<description>]`—where:
- `<version>` is in `X.Y.Z` format (e.g., `0.0.1`).
- `<owner>` is the lowercase username of the developer or team (e.g., `tom`).
- `<type>` is one of `feature`, `bugfix`, `hotfix`, or `release`.
- `[description]` is an optional lowercase alphanumeric descriptor with hyphens (e.g., `add-login`), except for CTO hotfixes which omit it.
- The `main` branch is the root branch.

This structure enables developer teams to organize their workflow effectively. Below is a recommended workflow for teams using GitGuru.

### 4.1 Team Workflow

#### 4.1.1. Initialize the Repository
Start by initializing a Git repository with GitGuru. This creates the `main` branch with an initial commit that stages all existing files.

    # Initialize in the current directory
    gitguru init

    # Or specify a directory
    gitguru init /path/to/repo

**Team Action:** The team lead or a designated member initializes the repository and pushes it to the remote (`gitguru push`) to establish the shared `main` branch.

#### 4.1.2. Establish a Release Cycle
For each development cycle (e.g., a new version like `0.0.1`), create a `release` branch from `main`. This branch serves as the base for all work in that version.

    # Team lead creates a release branch
    gitguru branch 0.0.1 team release

**Team Action:** The team lead creates the release branch (e.g., `0.0.1/team/release`) and pushes it to the remote (`gitguru push`). All team members then base their work on this release branch.

#### 4.1.3. Develop Features, Bugfixes, or Hotfixes
Team members create branches from the release branch for their tasks. Use `feature` for new functionality, `bugfix` for fixes in the current cycle, or `hotfix` for urgent fixes (typically from `main`).

    # Developer Tom creates a feature branch
    gitguru branch 0.0.1 tom feature user-auth

    # Developer Jane creates a bugfix branch
    gitguru branch 0.0.1 jane bugfix login-error

**Team Action:**
- Each developer works on their branch, using `gitguru commit "message"` to save changes and `gitguru push` to share progress with the team.
- Use `gitguru view` to inspect the branch tree and ensure alignment with the team’s structure.

#### 4.1.4. Integrate Work into the Release
Once a task is complete, merge the branch back into the release branch. GitGuru auto-commits any uncommitted changes in the target branch before merging.

    # Merge Tom's feature into the release branch
    gitguru merge 0.0.1/tom/feature/user-auth 0.0.1/team/release

**Team Action:**
- Developers (or a reviewer) switch to the release branch (`gitguru switch 0.0.1/team/release`), merge the completed branch, and push the updated release branch (`gitguru push`).
- Use `gitguru view` to verify the merge and check the updated tree.

#### 4.1.5. Finalize the Release
When all features and fixes for the version are complete, merge the release branch into `main` to prepare for deployment.

    # Merge the release branch into main
    gitguru switch main
    gitguru merge 0.0.1/team/release main

**Team Action:** The team lead merges the release branch into `main`, pushes it (`gitguru push`), and tags it appropriately (using standard Git commands). The `main` branch now reflects the new version.

#### 4.1.6. Clean Up
Remove completed branches to keep the repository tidy. Use `--force` for unmerged branches if necessary.

    # Delete Tom's feature branch
    gitguru delete 0.0.1/tom/feature/user-auth

**Team Action:** Developers delete their feature/bugfix branches after merging (`gitguru delete`), ensuring the branch tree remains clean. Use `gitguru view` to confirm.

#### 4.1.7. Handle Urgent Hotfixes
For critical issues in production, create a `hotfix` branch from `main`, fix the issue, and merge it back. The CTO can use specialized commands to streamline this process without descriptions.

    # CTO creates a hotfix branch directly from main
    gitguru cto-hotfix 0.0.2
    # ... fix the issue ...
    gitguru commit "Fix crash in login"
    gitguru cto-hotfix-push 0.0.2

**Team Action:** A designated member (e.g., the CTO) creates a hotfix branch directly from `main` using `cto-hotfix` (e.g., `0.0.2/cto/hotfix`), applies the fix, and uses `cto-hotfix-push` to merge it into `main` and push the changes. Optionally, backport the fix to the current release branch (e.g., `gitguru merge 0.0.2/cto/hotfix 0.0.1/team/release`).

### 4.2 Available Commands

Run `gitguru help` to see all commands:

- `init [git_dir]` - Initialize a new Git repository (defaults to current directory).
- `view [git_dir]` - Visualize the branch tree (defaults to current directory).
- `branch <version> <owner> <type> [desc]` - Create a new branch (feature/bugfix from release, hotfix/release from main).
- `merge <source> <target>` - Merge source into target (auto-commits changes).
- `commit <message>` - Commit changes.
- `push` - Push the current branch to origin.
- `switch <branch>` - Switch to a branch.
- `delete <branch1> [branch2] ... [--force]` - Delete one or more branches.
- `cto-hotfix <version>` - Create a CTO hotfix branch directly from main (e.g., `0.0.2/cto/hotfix`).
- `cto-hotfix-push <version>` - Merge the CTO hotfix branch into main and push it.

### 4.3 Tips

- Use a consistent `<version>` across the team for each release cycle (e.g., `0.0.1`).
- Assign `<owner>` as individual usernames or a team identifier (e.g., `team` for shared branches).
- Regularly use `gitguru view` to visualize branch relationships and commit history.
- Merge frequently into the release branch to avoid conflicts.
- Keep `main` stable by merging only tested release branches or hotfixes.
- Use descriptive `[description]` fields for feature/bugfix branches to clarify purpose (e.g., `user-auth`, `crash-fix`); CTO hotfixes omit this for simplicity.
- Push changes often (`gitguru push`) to collaborate effectively with the team.

## 5. License

This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
