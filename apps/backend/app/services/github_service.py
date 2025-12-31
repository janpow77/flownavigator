"""GitHub Integration Service.

Handles all GitHub operations including repository management,
branch operations, PR creation, and file staging.
"""

import base64
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.module_converter import GitHubIntegration


logger = logging.getLogger(__name__)


class GitHubError(Exception):
    """GitHub API error."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class Repository:
    """GitHub repository info."""

    name: str
    full_name: str
    default_branch: str
    private: bool
    url: str
    clone_url: str


@dataclass
class Branch:
    """GitHub branch info."""

    name: str
    sha: str
    protected: bool


@dataclass
class PullRequest:
    """GitHub PR info."""

    number: int
    title: str
    state: str
    url: str
    html_url: str
    head_branch: str
    base_branch: str
    mergeable: bool | None
    merged: bool


@dataclass
class Commit:
    """GitHub commit info."""

    sha: str
    message: str
    url: str
    author: str
    date: datetime


class GitHubService:
    """Service for GitHub operations.

    Supports:
    - Personal Access Token authentication
    - GitHub App authentication
    - Repository operations
    - Branch management
    - Pull request operations
    - File operations
    """

    API_BASE = "https://api.github.com"
    ACCEPT_HEADER = "application/vnd.github+json"
    API_VERSION = "2022-11-28"

    def __init__(
        self,
        access_token: str,
        api_base: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize GitHub service.

        Args:
            access_token: GitHub personal access token or app token
            api_base: Optional custom API base (for GitHub Enterprise)
            timeout: Request timeout in seconds
        """
        self.access_token = access_token
        self.api_base = api_base or self.API_BASE
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Accept": self.ACCEPT_HEADER,
                    "X-GitHub-Api-Version": self.API_VERSION,
                },
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make an API request.

        Args:
            method: HTTP method
            path: API path (without base URL)
            **kwargs: Additional request arguments

        Returns:
            Response JSON

        Raises:
            GitHubError: If request fails
        """
        client = await self._get_client()
        url = f"{self.api_base}{path}"

        try:
            response = await client.request(method, url, **kwargs)

            if response.status_code == 204:
                return {}

            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                message = error_data.get("message", f"HTTP {response.status_code}")
                raise GitHubError(message, response.status_code)

            return response.json() if response.content else {}

        except httpx.RequestError as e:
            raise GitHubError(f"Request failed: {e}") from e

    # ==========================================================================
    # Authentication & Validation
    # ==========================================================================

    async def validate_token(self) -> bool:
        """Validate the access token.

        Returns:
            True if token is valid
        """
        try:
            await self._request("GET", "/user")
            return True
        except GitHubError:
            return False

    async def get_authenticated_user(self) -> dict[str, Any]:
        """Get the authenticated user."""
        return await self._request("GET", "/user")

    # ==========================================================================
    # Repository Operations
    # ==========================================================================

    async def list_repositories(
        self,
        visibility: str = "all",
        per_page: int = 30,
    ) -> list[Repository]:
        """List repositories accessible to the authenticated user.

        Args:
            visibility: Filter by visibility (all, public, private)
            per_page: Results per page

        Returns:
            List of repositories
        """
        data = await self._request(
            "GET",
            "/user/repos",
            params={"visibility": visibility, "per_page": per_page},
        )
        return [
            Repository(
                name=r["name"],
                full_name=r["full_name"],
                default_branch=r["default_branch"],
                private=r["private"],
                url=r["url"],
                clone_url=r["clone_url"],
            )
            for r in data
        ]

    async def get_repository(self, owner: str, repo: str) -> Repository:
        """Get repository information.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository info
        """
        data = await self._request("GET", f"/repos/{owner}/{repo}")
        return Repository(
            name=data["name"],
            full_name=data["full_name"],
            default_branch=data["default_branch"],
            private=data["private"],
            url=data["url"],
            clone_url=data["clone_url"],
        )

    # ==========================================================================
    # Branch Operations
    # ==========================================================================

    async def list_branches(
        self,
        owner: str,
        repo: str,
        per_page: int = 30,
    ) -> list[Branch]:
        """List repository branches.

        Args:
            owner: Repository owner
            repo: Repository name
            per_page: Results per page

        Returns:
            List of branches
        """
        data = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/branches",
            params={"per_page": per_page},
        )
        return [
            Branch(
                name=b["name"],
                sha=b["commit"]["sha"],
                protected=b.get("protected", False),
            )
            for b in data
        ]

    async def get_branch(self, owner: str, repo: str, branch: str) -> Branch:
        """Get branch information.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name

        Returns:
            Branch info
        """
        data = await self._request("GET", f"/repos/{owner}/{repo}/branches/{branch}")
        return Branch(
            name=data["name"],
            sha=data["commit"]["sha"],
            protected=data.get("protected", False),
        )

    async def create_branch(
        self,
        owner: str,
        repo: str,
        branch_name: str,
        from_sha: str,
    ) -> Branch:
        """Create a new branch.

        Args:
            owner: Repository owner
            repo: Repository name
            branch_name: New branch name
            from_sha: SHA to branch from

        Returns:
            Created branch info
        """
        await self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/refs",
            json={
                "ref": f"refs/heads/{branch_name}",
                "sha": from_sha,
            },
        )
        return await self.get_branch(owner, repo, branch_name)

    async def delete_branch(self, owner: str, repo: str, branch: str) -> None:
        """Delete a branch.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name
        """
        await self._request(
            "DELETE",
            f"/repos/{owner}/{repo}/git/refs/heads/{branch}",
        )

    # ==========================================================================
    # File Operations
    # ==========================================================================

    async def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str | None = None,
    ) -> tuple[str, str]:
        """Get file content.

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            ref: Optional branch/tag/commit reference

        Returns:
            Tuple of (content, sha)
        """
        params = {"ref": ref} if ref else {}
        data = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/contents/{path}",
            params=params,
        )
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content, data["sha"]

    async def create_or_update_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str,
        sha: str | None = None,
    ) -> Commit:
        """Create or update a file.

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            content: File content
            message: Commit message
            branch: Branch name
            sha: File SHA (required for updates)

        Returns:
            Commit info
        """
        payload: dict[str, Any] = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
            "branch": branch,
        }
        if sha:
            payload["sha"] = sha

        data = await self._request(
            "PUT",
            f"/repos/{owner}/{repo}/contents/{path}",
            json=payload,
        )
        commit = data["commit"]
        return Commit(
            sha=commit["sha"],
            message=commit["message"],
            url=commit["url"],
            author=commit["author"]["name"],
            date=datetime.fromisoformat(commit["author"]["date"].replace("Z", "+00:00")),
        )

    async def create_files_in_commit(
        self,
        owner: str,
        repo: str,
        branch: str,
        files: list[dict[str, str]],
        message: str,
    ) -> Commit:
        """Create multiple files in a single commit.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name
            files: List of {"path": ..., "content": ...}
            message: Commit message

        Returns:
            Commit info
        """
        # Get the current commit SHA
        ref = await self._request("GET", f"/repos/{owner}/{repo}/git/ref/heads/{branch}")
        base_sha = ref["object"]["sha"]

        # Get the base tree
        base_commit = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/git/commits/{base_sha}",
        )
        base_tree_sha = base_commit["tree"]["sha"]

        # Create blobs for each file
        tree_items = []
        for file in files:
            blob = await self._request(
                "POST",
                f"/repos/{owner}/{repo}/git/blobs",
                json={
                    "content": file["content"],
                    "encoding": "utf-8",
                },
            )
            tree_items.append({
                "path": file["path"],
                "mode": "100644",
                "type": "blob",
                "sha": blob["sha"],
            })

        # Create new tree
        new_tree = await self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/trees",
            json={
                "base_tree": base_tree_sha,
                "tree": tree_items,
            },
        )

        # Create commit
        commit = await self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/commits",
            json={
                "message": message,
                "tree": new_tree["sha"],
                "parents": [base_sha],
            },
        )

        # Update branch reference
        await self._request(
            "PATCH",
            f"/repos/{owner}/{repo}/git/refs/heads/{branch}",
            json={"sha": commit["sha"]},
        )

        return Commit(
            sha=commit["sha"],
            message=commit["message"],
            url=commit["url"],
            author=commit["author"]["name"],
            date=datetime.fromisoformat(commit["author"]["date"].replace("Z", "+00:00")),
        )

    # ==========================================================================
    # Pull Request Operations
    # ==========================================================================

    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str,
        body: str | None = None,
        draft: bool = False,
    ) -> PullRequest:
        """Create a pull request.

        Args:
            owner: Repository owner
            repo: Repository name
            title: PR title
            head: Head branch
            base: Base branch
            body: PR description
            draft: Create as draft

        Returns:
            Pull request info
        """
        data = await self._request(
            "POST",
            f"/repos/{owner}/{repo}/pulls",
            json={
                "title": title,
                "head": head,
                "base": base,
                "body": body or "",
                "draft": draft,
            },
        )
        return PullRequest(
            number=data["number"],
            title=data["title"],
            state=data["state"],
            url=data["url"],
            html_url=data["html_url"],
            head_branch=data["head"]["ref"],
            base_branch=data["base"]["ref"],
            mergeable=data.get("mergeable"),
            merged=data.get("merged", False),
        )

    async def update_pull_request(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        title: str | None = None,
        body: str | None = None,
        state: str | None = None,
    ) -> PullRequest:
        """Update a pull request.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            title: New title
            body: New body
            state: New state (open, closed)

        Returns:
            Updated pull request info
        """
        payload = {}
        if title:
            payload["title"] = title
        if body:
            payload["body"] = body
        if state:
            payload["state"] = state

        data = await self._request(
            "PATCH",
            f"/repos/{owner}/{repo}/pulls/{pr_number}",
            json=payload,
        )
        return PullRequest(
            number=data["number"],
            title=data["title"],
            state=data["state"],
            url=data["url"],
            html_url=data["html_url"],
            head_branch=data["head"]["ref"],
            base_branch=data["base"]["ref"],
            mergeable=data.get("mergeable"),
            merged=data.get("merged", False),
        )

    async def add_labels(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        labels: list[str],
    ) -> None:
        """Add labels to an issue/PR.

        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue/PR number
            labels: Labels to add
        """
        await self._request(
            "POST",
            f"/repos/{owner}/{repo}/issues/{issue_number}/labels",
            json={"labels": labels},
        )

    async def request_reviewers(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        reviewers: list[str],
    ) -> None:
        """Request reviewers for a PR.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            reviewers: Reviewer usernames
        """
        await self._request(
            "POST",
            f"/repos/{owner}/{repo}/pulls/{pr_number}/requested_reviewers",
            json={"reviewers": reviewers},
        )

    async def merge_pull_request(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        merge_method: str = "squash",
        commit_message: str | None = None,
    ) -> bool:
        """Merge a pull request.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            merge_method: Merge method (merge, squash, rebase)
            commit_message: Optional commit message

        Returns:
            True if merged successfully
        """
        payload: dict[str, Any] = {"merge_method": merge_method}
        if commit_message:
            payload["commit_message"] = commit_message

        try:
            await self._request(
                "PUT",
                f"/repos/{owner}/{repo}/pulls/{pr_number}/merge",
                json=payload,
            )
            return True
        except GitHubError as e:
            if e.status_code == 405:
                # Not mergeable
                return False
            raise

    async def add_comment(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        body: str,
    ) -> dict[str, Any]:
        """Add a comment to an issue/PR.

        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue/PR number
            body: Comment body

        Returns:
            Comment data
        """
        return await self._request(
            "POST",
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            json={"body": body},
        )


async def create_github_service_from_integration(
    integration: GitHubIntegration,
    db: AsyncSession,
) -> GitHubService:
    """Create a GitHubService from a GitHubIntegration model.

    Args:
        integration: GitHub integration configuration
        db: Database session

    Returns:
        Configured GitHubService
    """
    # TODO: Implement proper decryption
    access_token = integration.access_token_encrypted or ""

    # Check for GitHub Enterprise
    api_base = integration.config.get("api_base") if integration.config else None

    return GitHubService(
        access_token=access_token,
        api_base=api_base,
    )
