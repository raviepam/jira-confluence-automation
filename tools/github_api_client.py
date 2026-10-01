import base64
import json
import os
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


class GitHubAPIError(RuntimeError):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class ContentTooLargeError(ValueError):
    pass


def repository_api_path(repository: str) -> str:
    parts = repository.split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError("Repository must use the OWNER/REPOSITORY format.")
    owner, name = parts
    return f"/repos/{quote(owner, safe='')}/{quote(name, safe='')}"


class GitHubAPIClient:
    def __init__(self, token: str, api_url: Optional[str] = None, timeout: int = 20):
        self.api_url = (api_url or os.getenv("GITHUB_API_URL") or "https://api.github.com").rstrip("/")
        self.token = token
        self.timeout = timeout

    @classmethod
    def from_environment(cls, api_url: Optional[str] = None):
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("Set GITHUB_TOKEN to a GitHub token with repository read access.")
        return cls(token, api_url)

    def get_json(self, endpoint: str, params: Optional[dict[str, str]] = None):
        url = f"{self.api_url}{endpoint}"
        if params:
            url = f"{url}?{urlencode(params)}"
        request = Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "pr-reviewer-tools",
            },
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            try:
                message = json.loads(body).get("message", body)
            except (json.JSONDecodeError, AttributeError):
                message = body
            if error.code in (403, 429) and (
                error.headers.get("X-RateLimit-Remaining") == "0" or error.code == 429
            ):
                retry_after = error.headers.get("Retry-After")
                reset = error.headers.get("X-RateLimit-Reset")
                details = ", ".join(
                    item for item in (f"Retry-After: {retry_after}" if retry_after else None,
                                      f"reset epoch: {reset}" if reset else None)
                    if item
                )
                suffix = f" ({details})" if details else ""
                raise GitHubAPIError(f"GitHub API rate limit exceeded{suffix}.", error.code) from error
            if error.code == 403:
                message = f"GitHub denied access; check token permissions. {message}"
            elif error.code == 404:
                message = f"GitHub resource was not found or is not accessible. {message}"
            raise GitHubAPIError(f"GitHub API returned HTTP {error.code}: {message}", error.code) from error
        except (URLError, TimeoutError) as error:
            raise GitHubAPIError(f"GitHub API request failed: {error}") from error
        except json.JSONDecodeError as error:
            raise GitHubAPIError("GitHub API returned invalid JSON.") from error

    def get_file_text(self, repository: str, path: str, ref: str, max_bytes: int) -> tuple[str, int]:
        if path.startswith("/") or ".." in path.split("/"):
            raise ValueError(f"Repository paths must be relative and cannot contain '..': {path}")
        endpoint = f"{repository_api_path(repository)}/contents/{quote(path, safe='/')}"
        result = self.get_json(endpoint, {"ref": ref})
        if not isinstance(result, dict) or result.get("type") != "file":
            raise ValueError(f"GitHub path is not a file: {path}")
        size = int(result.get("size", 0))
        if size > max_bytes:
            raise ContentTooLargeError(f"File is {size} bytes; per-file limit is {max_bytes} bytes.")
        if result.get("encoding") != "base64" or not result.get("content"):
            raise ValueError(f"GitHub did not return inline text content for: {path}")
        content = base64.b64decode(result["content"]).decode("utf-8")
        return content, size