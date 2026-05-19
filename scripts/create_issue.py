import argparse
import json
import os
from datetime import date, datetime, timezone
from urllib.parse import quote
from urllib.request import Request, urlopen

from dotenv import load_dotenv

try:
    from scripts.render_markdown import render_issue_body
except ModuleNotFoundError:
    from render_markdown import render_issue_body


def build_weekly_title(d: date) -> str:
    iso_year, iso_week, _ = d.isocalendar()
    return f"Weekly GitHub Trending - {iso_year}-W{iso_week:02d}"


def build_search_query(repo: str, title: str) -> str:
    return f'repo:{repo} is:issue is:open in:title "{title}"'


def github_api_request(method: str, url: str, token: str, payload=None):
    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = Request(url, data=data, headers=headers, method=method)
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def issue_exists(repo: str, token: str, title: str) -> bool:
    q = build_search_query(repo, title)
    url = f"https://api.github.com/search/issues?q={quote(q)}"
    data = github_api_request("GET", url, token)
    return data.get("total_count", 0) > 0


def create_issue(repo: str, token: str, title: str, body: str):
    url = f"https://api.github.com/repos/{repo}/issues"
    payload = {"title": title, "body": body, "labels": ["github-trending", "weekly-report"]}
    return github_api_request("POST", url, token, payload)


def main():
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()

    token = os.environ["DEPLOY_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]

    with open(args.input, "r", encoding="utf-8") as f:
        items = json.load(f)

    now = datetime.now(timezone.utc)
    title = build_weekly_title(now.date())

    if issue_exists(repo, token, title):
        print("Issue already exists for this ISO week; skipping.")
        return

    body = render_issue_body(items=items, top=args.top, generated_at=now.isoformat())

    try:
        create_issue(repo, token, title, body)
    except Exception:
        create_issue(repo, token, title, body)


if __name__ == "__main__":
    main()
