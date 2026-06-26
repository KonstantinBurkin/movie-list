"""GitHub sync module using PyGithub API - works on Streamlit Cloud."""

from pathlib import Path

from github import Github, GithubException


def create_pr_with_movie(
    movie_title: str, movie_year: int, github_token: str, repo_name: str = None
) -> tuple[bool, str]:
    """
    Create a PR with new movie using GitHub API.

    Args:
        movie_title: Movie title
        movie_year: Movie year
        github_token: GitHub personal access token
        repo_name: GitHub repo in format "owner/repo" (auto-detected if None)

    Returns:
        (success, result_message)
    """
    try:
        # Initialize GitHub client
        g = Github(github_token)

        # Auto-detect repo if not provided
        if repo_name is None:
            repo_name = get_repo_info()
            if repo_name is None:
                repo_name = "KonstantinBurkin/movie-list"  # Fallback

        repo = g.get_repo(repo_name)

        # Generate branch name
        safe_title = "".join(c if c.isalnum() else "-" for c in movie_title.lower())
        branch_name = f"add-movie-{safe_title}-{movie_year}"

        # Get main branch
        main_branch = repo.get_branch("main")
        base_sha = main_branch.commit.sha

        # Create new branch
        repo.create_git_ref(f"refs/heads/{branch_name}", base_sha)

        # Read updated parquet file
        parquet_path = Path("./data/movies_df.parquet")
        with open(parquet_path, "rb") as f:
            content = f.read()

        # Get current file SHA to update it
        try:
            current_file = repo.get_contents("data/movies_df.parquet", ref="main")
            file_sha = current_file.sha
        except GithubException:
            file_sha = None

        # Update file in new branch
        commit_message = f"Add movie: {movie_title} ({movie_year})\n\nCo-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

        repo.update_file(
            path="data/movies_df.parquet",
            message=commit_message,
            content=content,
            sha=file_sha,
            branch=branch_name,
        )

        # Create pull request
        pr_title = f"Add movie: {movie_title} ({movie_year})"
        pr_body = f"""Automatically adding movie via Streamlit app.

**Movie:** {movie_title}
**Year:** {movie_year}

🤖 Generated with [Claude Code](https://claude.com/claude-code)
"""

        pr = repo.create_pull(
            title=pr_title, body=pr_body, head=branch_name, base="main"
        )

        # Enable auto-merge if available
        try:
            pr.enable_automerge(merge_method="MERGE")
        except Exception:
            # Auto-merge might not be available, that's ok
            pass

        return True, pr.html_url

    except GithubException as e:
        return False, f"GitHub API error: {e.data.get('message', str(e))}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def get_repo_info():
    """Helper to detect current repo from git config."""
    try:
        import subprocess

        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=True,
        )
        url = result.stdout.strip()
        # Parse owner/repo from URL
        if "github.com" in url:
            parts = url.replace(".git", "").split("/")
            return f"{parts[-2]}/{parts[-1]}"
    except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
        pass
    return None
