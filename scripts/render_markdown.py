def render_issue_body(items, top, generated_at):
    lines = [
        "# Weekly GitHub Trending",
        "",
        f"- Generated at: {generated_at}",
        "- Source: GitHub Trending (weekly)",
        f"- Top {top}",
        "",
        "| # | Repository | Language | Stars | Forks | Summary |",
        "|---|---|---|---:|---:|---|",
    ]

    for item in items:
        repo_link = f"[{item['repo']}]({item['url']})"
        lines.append(
            f"| {item['rank']} | {repo_link} | {item['language'] or '-'} | {item['stars']} | {item['forks']} | {item['summary'] or '-'} |"
        )

    lines.extend(["", "_This issue is generated automatically._"])
    return "\n".join(lines)
