import ast
import base64
import json
import os
import re
from pathlib import Path
from pprint import pformat
from typing import Any

import requests
from dotenv import load_dotenv

SPRINTS = (27, 28)
RAW_OUTPUT_PATH = Path("sp/data_raw_27_28.json")
SP_DATA_PATH = Path("sp/data.py")
SPRINT_PATTERN = re.compile(r"name=Tools\.(\d+)")
SPRINT_FALLBACK_PATTERN = re.compile(r"Tools\.(\d+)")


def build_jira_headers() -> tuple[str, dict]:
    """Build Jira URL and auth headers from environment."""
    load_dotenv()

    jira_url = os.getenv("JIRA_URL")
    jira_host = os.getenv("JIRA_HOST")
    jira_user_name = os.getenv("JIRA_USER_NAME")
    jira_user_pass = os.getenv("JIRA_USER_PASS")

    missing_vars = [
        name
        for name, value in (
            ("JIRA_URL", jira_url),
            ("JIRA_HOST", jira_host),
            ("JIRA_USER_NAME", jira_user_name),
            ("JIRA_USER_PASS", jira_user_pass),
        )
        if not value
    ]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    auth_string = base64.b64encode(f"{jira_user_name}:{jira_user_pass}".encode()).decode()
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=UTF-8",
        "host": jira_host,
        "Authorization": f"Basic {auth_string}",
    }
    return jira_url, headers


def parse_sprint_number(raw_sprint: Any) -> int | str:
    """Extract sprint number from Jira customfield_10005."""
    if raw_sprint is None:
        return ""

    detected_numbers: list[int] = []
    values = raw_sprint if isinstance(raw_sprint, list) else [raw_sprint]
    for value in values:
        if isinstance(value, dict):
            name = value.get("name")
            if isinstance(name, str):
                direct_match = re.search(r"Tools\.(\d+)", name)
                if direct_match:
                    detected_numbers.append(int(direct_match.group(1)))
            value_as_text = json.dumps(value, ensure_ascii=False)
        else:
            value_as_text = str(value)

        match = SPRINT_PATTERN.search(value_as_text)
        if match:
            detected_numbers.append(int(match.group(1)))
            continue

        fallback_match = SPRINT_FALLBACK_PATTERN.search(value_as_text)
        if fallback_match:
            detected_numbers.append(int(fallback_match.group(1)))

    preferred = [number for number in detected_numbers if number in SPRINTS]
    if preferred:
        return max(preferred)
    if detected_numbers:
        return detected_numbers[-1]
    return ""


def fetch_sprint_issues() -> list[dict]:
    """Fetch all issues from Tools.27 and Tools.28 sprints."""
    jira_url, headers = build_jira_headers()
    url = f"{jira_url}/search"
    jql = f"project = ADSTOOLS AND sprint in ({', '.join(f'Tools.{n}' for n in SPRINTS)})"

    issues: list[dict] = []
    start_at = 0
    max_results = 100
    fields = "assignee,customfield_10002,customfield_10005"

    while True:
        params = {
            "jql": jql,
            "fields": fields,
            "startAt": start_at,
            "maxResults": max_results,
        }
        response = requests.get(url, headers=headers, params=params, verify=False, timeout=30)

        if response.status_code != 200:
            raise RuntimeError(f"Jira request failed: {response.status_code} {response.text}")

        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise RuntimeError("Jira returned invalid JSON response") from exc

        page_issues = payload.get("issues", [])
        issues.extend(page_issues)

        total = payload.get("total", 0)
        start_at += len(page_issues)
        if not page_issues or start_at >= total:
            break

    return issues


def normalize_issues(issues: list[dict]) -> list[dict]:
    """Convert Jira issues to SP-ready structure."""
    normalized: list[dict] = []
    for issue in issues:
        fields = issue.get("fields", {})
        assignee_data = fields.get("assignee") or {}
        assignee_name = assignee_data.get("displayName", "") if isinstance(assignee_data, dict) else ""
        story_points = fields.get("customfield_10002")
        sprint_number = parse_sprint_number(fields.get("customfield_10005"))

        normalized.append(
            {
                "task": issue.get("key", ""),
                "assignee": assignee_name or "",
                "story_points": story_points,
                "sprint": sprint_number,
            }
        )
    return normalized


def save_raw_data(data: list[dict]) -> None:
    """Save normalized sprint data to JSON."""
    RAW_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RAW_OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def prepend_to_sp_data(new_entries: list[dict]) -> None:
    """Prepend fetched entries to sp/data.py list."""
    if not SP_DATA_PATH.exists():
        raise FileNotFoundError(f"File not found: {SP_DATA_PATH}")

    content = SP_DATA_PATH.read_text(encoding="utf-8")
    if "=" not in content:
        raise ValueError("Invalid sp/data.py format: expected assignment to data")

    _, raw_data_part = content.split("=", 1)
    existing_data = ast.literal_eval(raw_data_part.strip())
    if not isinstance(existing_data, list):
        raise ValueError("Invalid sp/data.py format: data must be a list")

    new_tasks = [item.get("task", "") for item in new_entries]
    top_tasks = [item.get("task", "") for item in existing_data[: len(new_entries)]]
    # Avoid duplicating the latest export block on repeated script runs.
    if top_tasks == new_tasks:
        existing_data = existing_data[len(new_entries) :]

    combined = new_entries + existing_data
    formatted = f"data = {pformat(combined, width=120, sort_dicts=False)}\n"
    SP_DATA_PATH.write_text(formatted, encoding="utf-8")


def main() -> int:
    try:
        issues = fetch_sprint_issues()
        normalized = normalize_issues(issues)
        save_raw_data(normalized)
        prepend_to_sp_data(normalized)
        print(f"Saved raw data to {RAW_OUTPUT_PATH}")
        print(f"Prepended {len(normalized)} records to {SP_DATA_PATH}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
