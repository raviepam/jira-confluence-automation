import argparse
import fnmatch
import json
from pathlib import Path
from typing import List, Optional

from github_api_client import (
    ContentTooLargeError,
    GitHubAPIClient,
    GitHubAPIError,
    repository_api_path,
)
from github_pr_api import fetch_pull_request_data


DEFAULT_EXCLUDES = ("**/node_modules/**", "**/generated/**", "**/dist/**", "**/build/**")


def is_excluded(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def collect_pull_request_context(
    client: GitHubAPIClient,
    repository: str,
    pull_number: int,
    extra_context_paths: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    max_files: int = 100,
    max_file_bytes: int = 100_000,
    max_context_bytes: int = 1_000_000,
) -> dict:
    pull_data = fetch_pull_request_data(client, repository, pull_number)
    exclusions = list(DEFAULT_EXCLUDES) + (exclude_patterns or [])
    changed_by_path = {item["path"]: item for item in pull_data["changed_files"]}
    paths = list(changed_by_path)
    for path in [".pr-reviewer.yml", *(extra_context_paths or [])]:
        if path not in changed_by_path and path not in paths:
            paths.append(path)

    included = []
    skipped = []
    total_bytes = 0
    for path in paths:
        changed = changed_by_path.get(path)
        if is_excluded(path, exclusions):
            skipped.append({"path": path, "reason": "excluded by path pattern"})
            continue
        if len(included) >= max_files:
            skipped.append({"path": path, "reason": "maximum context file count reached"})
            continue
        if changed:
            item = {
                "path": path,
                "kind": "changed",
                "status": changed["status"],
                "patch": None,
                "content": None,
                "patch_size_bytes": 0,
                "content_size_bytes": 0,
            }
            patch = changed.get("patch")
            if patch:
                patch_size = len(patch.encode("utf-8"))
                if total_bytes + patch_size <= max_context_bytes:
                    item["patch"] = patch
                    item["patch_size_bytes"] = patch_size
                    total_bytes += patch_size
                else:
                    item["patch_skipped_reason"] = "maximum aggregate context size reached"
                    skipped.append({"path": path, "reason": item["patch_skipped_reason"]})

            if changed["status"] == "removed":
                item["content_skipped_reason"] = "file was deleted in this pull request"
                skipped.append({"path": path, "reason": item["content_skipped_reason"]})
                included.append(item)
                continue

            try:
                text, size = client.get_file_text(
                    repository, path, pull_data["head_sha"], max_file_bytes
                )
            except ContentTooLargeError as error:
                item["content_skipped_reason"] = str(error)
            except GitHubAPIError as error:
                if error.status_code == 404:
                    item["content_skipped_reason"] = "file content was not found at the pull-request head"
                else:
                    raise
            except (UnicodeDecodeError, ValueError) as error:
                item["content_skipped_reason"] = f"not readable as bounded UTF-8 text: {error}"
            else:
                if total_bytes + size > max_context_bytes:
                    item["content_skipped_reason"] = "maximum aggregate context size reached"
                else:
                    item["content"] = text
                    item["content_size_bytes"] = size
                    total_bytes += size
            if "content_skipped_reason" in item:
                skipped.append({"path": path, "reason": item["content_skipped_reason"]})
            included.append(item)
            continue

        try:
            text, size = client.get_file_text(
                repository, path, pull_data["head_sha"], max_file_bytes
            )
        except ContentTooLargeError as error:
            skipped.append({"path": path, "reason": str(error)})
            continue
        except GitHubAPIError as error:
            if error.status_code == 404:
                skipped.append({"path": path, "reason": "optional context file was not found"})
                continue
            raise
        except (UnicodeDecodeError, ValueError) as error:
            skipped.append({"path": path, "reason": f"not readable as bounded UTF-8 text: {error}"})
            continue
        if total_bytes + size > max_context_bytes:
            skipped.append({"path": path, "reason": "maximum aggregate context size reached"})
            continue
        total_bytes += size
        included.append(
            {
                "path": path,
                "kind": "repository_context",
                "status": "unchanged",
                "patch": None,
                "content": text,
                "content_size_bytes": size,
                "patch_size_bytes": 0,
            }
        )

    latest_pull = client.get_json(f"{repository_api_path(repository)}/pulls/{pull_number}")
    if latest_pull["head"]["sha"] != pull_data["head_sha"]:
        raise ValueError("Pull request head changed during context collection; rerun against the latest revision.")

    return {
        "repository": repository,
        "pull_number": pull_number,
        "head_sha": pull_data["head_sha"],
        "base_sha": pull_data["base_sha"],
        "files": included,
        "skipped": skipped,
        "limits": {
            "max_files": max_files,
            "max_file_bytes": max_file_bytes,
            "max_context_bytes": max_context_bytes,
            "included_bytes": total_bytes,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect bounded, revision-pinned PR and repository context as JSON."
    )
    parser.add_argument("repository", help="GitHub repository in OWNER/REPOSITORY format")
    parser.add_argument("pull_number", type=int)
    parser.add_argument("--api-url", help="GitHub API base URL; defaults to GITHUB_API_URL or github.com")
    parser.add_argument("--context-path", action="append", default=[], help="Extra ADR, schema, manifest, or dependency file to include")
    parser.add_argument("--exclude", action="append", default=[], help="Additional fnmatch path pattern to exclude")
    parser.add_argument("--max-files", type=int, default=100)
    parser.add_argument("--max-file-bytes", type=int, default=100_000)
    parser.add_argument("--max-context-bytes", type=int, default=1_000_000)
    parser.add_argument("--output", default="-", help="JSON output path, or '-' for stdout")
    args = parser.parse_args()

    try:
        if min(args.max_files, args.max_file_bytes, args.max_context_bytes) <= 0:
            raise ValueError("Context limits must be greater than zero.")
        client = GitHubAPIClient.from_environment(args.api_url)
        context = collect_pull_request_context(
            client,
            args.repository,
            args.pull_number,
            args.context_path,
            args.exclude,
            args.max_files,
            args.max_file_bytes,
            args.max_context_bytes,
        )
        output = json.dumps(context, indent=2) + "\n"
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