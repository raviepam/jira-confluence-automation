# Module 12 Completion Report

## Instruction File
- Filename: instructions/use-github-pr-api.agent.md

```markdown
- Use `tools/github_pr_api.py` when a workflow needs GitHub pull-request metadata and a paginated list of changed files with patches.
- Follow `./use-github_api_client.agent.md` for GitHub authentication, API host selection, rate limits, permissions, and error handling.
- Set `GITHUB_TOKEN` in the process environment with minimum repository read access; never pass or print the token.
- Run `python3 tools/github_pr_api.py OWNER/REPOSITORY PULL_NUMBER`. Add `--output path.json` to save JSON instead of writing it to stdout.
- Use `--api-url` only for an approved GitHub API host, `--page-size` from 1 to 100 when pagination needs tuning, and `--max-pages` to bound retrieval. Defaults are the environment/default API URL, 100 items per page, and 30 pages.
- Treat the returned `head_sha` as the revision the data describes. The tool checks the head before and after pagination; if it changes, rerun rather than combining results from different revisions.
- Consume `changed_files` entries using `path`, `status`, `additions`, `deletions`, `changes`, and `patch`. A patch may be absent for binary, oversized, or otherwise unsupported files.
- Handle non-zero CLI exits as retrieval failures. Check token permissions, repository and pull-request identifiers, pagination limits, and rate-limit guidance before retrying.
- Treat saved PR JSON and patches as source-code data: keep output in an approved location and do not commit it unless explicitly authorized.
- Use this tool for read-only retrieval; it does not post comments, change pull requests, or modify repository contents on GitHub.
```

## Script File
- Filename: tools/github_pr_api.py
- Language: Python

```python
import argparse
import json
from pathlib import Path

from github_api_client import GitHubAPIClient, GitHubAPIError, repository_api_path


def fetch_pull_request_data(
    client: GitHubAPIClient,
    repository: str,
    pull_number: int,
    page_size: int = 100,
    max_pages: int = 30,
) -> dict:
    if pull_number <= 0:
        raise ValueError("Pull request number must be greater than zero.")
    if not 1 <= page_size <= 100:
        raise ValueError("Page size must be between 1 and 100.")
    repo_path = repository_api_path(repository)
    pull_path = f"{repo_path}/pulls/{pull_number}"
    pull = client.get_json(pull_path)
    head_sha = pull["head"]["sha"]
    changed_files = []

    for page in range(1, max_pages + 1):
        page_files = client.get_json(
            f"{pull_path}/files",
            {"per_page": str(page_size), "page": str(page)},
        )
        if not isinstance(page_files, list):
            raise ValueError("GitHub returned an invalid pull-request files response.")
        changed_files.extend(
            {
                "path": item["filename"],
                "status": item["status"],
                "additions": item.get("additions", 0),
                "deletions": item.get("deletions", 0),
                "changes": item.get("changes", 0),
                "patch": item.get("patch"),
            }
            for item in page_files
        )
        if len(page_files) < page_size:
            break
    else:
        raise ValueError(f"Pull request file listing exceeded the {max_pages}-page limit.")

    latest_pull = client.get_json(pull_path)
    if latest_pull["head"]["sha"] != head_sha:
        raise ValueError("Pull request head changed during retrieval; rerun against the latest revision.")

    return {
        "repository": repository,
        "pull_number": pull_number,
        "title": pull.get("title", ""),
        "state": pull.get("state", ""),
        "base_ref": pull["base"]["ref"],
        "base_sha": pull["base"]["sha"],
        "head_ref": pull["head"]["ref"],
        "head_sha": head_sha,
        "changed_files": changed_files,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch pull-request metadata and paginated changed-file patches from GitHub."
    )
    parser.add_argument("repository", help="GitHub repository in OWNER/REPOSITORY format")
    parser.add_argument("pull_number", type=int)
    parser.add_argument("--api-url", help="GitHub API base URL; defaults to GITHUB_API_URL or github.com")
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=30)
    parser.add_argument("--output", default="-", help="JSON output path, or '-' for stdout")
    args = parser.parse_args()

    try:
        client = GitHubAPIClient.from_environment(args.api_url)
        data = fetch_pull_request_data(
            client, args.repository, args.pull_number, args.page_size, args.max_pages
        )
        output = json.dumps(data, indent=2) + "\n"
        if args.output == "-":
            print(output, end="")
        else:
            destination = Path(args.output)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(output, encoding="utf-8")
    except (GitHubAPIError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
```

## Script Execution Output
```text
usage: github_pr_api.py [-h] [--api-url API_URL] [--page-size PAGE_SIZE]
                        [--max-pages MAX_PAGES] [--output OUTPUT]
                        repository pull_number

Fetch pull-request metadata and paginated changed-file patches from GitHub.

positional arguments:
  repository            GitHub repository in OWNER/REPOSITORY format
  pull_number

optional arguments:
  -h, --help            show this help message and exit
  --api-url API_URL     GitHub API base URL; defaults to GITHUB_API_URL or
                        github.com
  --page-size PAGE_SIZE
  --max-pages MAX_PAGES
  --output OUTPUT       JSON output path, or '-' for stdout
```
