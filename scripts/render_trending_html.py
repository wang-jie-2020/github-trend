import argparse
import html
from pathlib import Path
from typing import Any, Mapping, Sequence

from scripts.trending_html_contracts import load_reader_inputs, validate_collection, validate_summaries


OUTPUT_FILENAME = "trending.html"


def render_html(collection: Mapping[str, Any], summaries: Mapping[str, Any]) -> str:
    collection = validate_collection(collection)
    summaries = validate_summaries(summaries, collection)
    summaries_by_repo = {summary["repo"]: summary for summary in summaries["summaries"]}
    cards = "\n".join(
        _render_card(repository, summaries_by_repo[repository["repo"]], len(collection["repositories"]))
        for repository in collection["repositories"]
    )
    title = "GitHub Weekly Trending"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
{_css()}
  </style>
</head>
<body>
  <main class="reader-deck" aria-label="GitHub Weekly Trending reader">
{cards}
  </main>
  <nav class="reader-nav" aria-label="Reader navigation">
    <button type="button" data-prev aria-label="Previous repository">Previous</button>
    <span data-progress>1 / {len(collection['repositories'])}</span>
    <button type="button" data-next aria-label="Next repository">Next</button>
  </nav>
  <script>
{_javascript()}
  </script>
</body>
</html>
"""


def render_trending_html(input_dir: Path) -> Path:
    collection, summaries = load_reader_inputs(input_dir)
    output_path = input_dir / OUTPUT_FILENAME
    output_path.write_text(render_html(collection, summaries), encoding="utf-8")
    return output_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    args = parser.parse_args(argv)

    output_path = render_trending_html(Path(args.input_dir))
    print(output_path)
    return 0


def _render_card(repository: Mapping[str, Any], summary: Mapping[str, Any], total: int) -> str:
    repo = _escape(repository["repo"])
    release = _release_label(repository["latest_release"])
    topics = repository["topics"] or ["No topics listed"]
    readme_note = ""
    if summary["readme_status"] != "ok":
        readme_note = f'<p class="readme-note">README {summary["readme_status"]}: {_escape(summary["readme_error"])}</p>'

    key_points = "\n".join(f"          <li>{_escape(point)}</li>" for point in summary["key_points"])
    topic_tags = "".join(f'<span class="topic">{_escape(topic)}</span>' for topic in topics)

    return f"""    <section class="reader-card" id="repo-{repository['rank']}" data-card aria-label="{repo}">
      <div class="card-shell">
        <aside class="card-facts">
          <p class="eyebrow">Repository {repository['rank']} of {total}</p>
          <p class="rank">#{repository['rank']}</p>
          <h1><a href="{_escape(repository['url'])}">{repo}</a></h1>
          <p class="description">{_escape(repository['trending_description'])}</p>
          <dl class="metrics">
            <div><dt>Language</dt><dd>{_escape(repository['language'])}</dd></div>
            <div><dt>Stars</dt><dd>{int(repository['stars']):,}</dd></div>
            <div><dt>Forks</dt><dd>{int(repository['forks']):,} forks</dd></div>
          </dl>
        </aside>
        <section class="card-details">
          <p class="section-label">README summary</p>
          <h2>{_escape(summary['summary'])}</h2>
          {readme_note}
          <div class="detail-grid">
            <section>
              <h3>Why it matters</h3>
              <p>{_escape(summary['why_it_matters'])}</p>
            </section>
            <section>
              <h3>Best for</h3>
              <p>{_escape(summary['best_for'])}</p>
            </section>
          </div>
          <section>
            <h3>Key points</h3>
            <ul>
{key_points}
            </ul>
          </section>
          <section class="metadata">
            <h3>Repository metadata</h3>
            <dl>
              <div><dt>API description</dt><dd>{_escape(repository['api_description'])}</dd></div>
              <div><dt>Topics</dt><dd>{topic_tags}</dd></div>
              <div><dt>License</dt><dd>{_optional(repository['license'])}</dd></div>
              <div><dt>Homepage</dt><dd>{_link_or_placeholder(repository['homepage'])}</dd></div>
              <div><dt>Pushed</dt><dd>{_escape(repository['pushed_timestamp'])}</dd></div>
              <div><dt>Latest release</dt><dd>{release}</dd></div>
            </dl>
          </section>
        </section>
      </div>
    </section>"""


def _css() -> str:
    return """    :root {
      color-scheme: light;
      --page: #f4f6f3;
      --ink: #17211d;
      --muted: #69766f;
      --line: #dce3dd;
      --panel: #ffffff;
      --accent: #476c5a;
      --accent-soft: #e8f0eb;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--page);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .reader-deck { scroll-snap-type: y mandatory; overflow-y: auto; height: 100vh; }
    .reader-card { min-height: 100vh; padding: 32px; display: grid; place-items: center; scroll-snap-align: start; }
    .card-shell {
      width: min(1120px, 100%);
      min-height: min(760px, calc(100vh - 64px));
      display: grid;
      grid-template-columns: minmax(280px, 0.9fr) minmax(0, 1.4fr);
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 28px;
      box-shadow: 0 24px 70px rgba(33, 48, 40, 0.08);
      overflow: hidden;
    }
    .card-facts { padding: 48px; border-right: 1px solid var(--line); background: linear-gradient(180deg, #fbfcfb, #eef4ef); }
    .card-details { padding: 48px; display: grid; gap: 22px; }
    .eyebrow, .section-label { color: var(--accent); font-size: 0.78rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; }
    .rank { font-size: clamp(4rem, 12vw, 8rem); line-height: 0.85; margin: 32px 0; font-weight: 800; color: var(--accent); }
    h1, h2, h3, p { margin-top: 0; }
    h1 { font-size: clamp(2rem, 4vw, 3.5rem); line-height: 1; overflow-wrap: anywhere; }
    h2 { font-size: clamp(1.8rem, 3vw, 3rem); line-height: 1.08; }
    h3 { font-size: 0.9rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); }
    a { color: var(--ink); text-decoration-thickness: 0.08em; text-underline-offset: 0.18em; }
    .description, .card-details p, li, dd { color: var(--muted); line-height: 1.6; }
    .metrics, .metadata dl { display: grid; gap: 14px; }
    .metrics div, .metadata dl div { padding-top: 14px; border-top: 1px solid var(--line); }
    dt { color: var(--muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; }
    dd { margin: 4px 0 0; color: var(--ink); }
    .detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    ul { margin: 0; padding-left: 1.2rem; }
    .topic { display: inline-block; margin: 0 6px 6px 0; padding: 4px 9px; border-radius: 999px; background: var(--accent-soft); color: var(--accent); font-size: 0.84rem; }
    .readme-note { padding: 12px 14px; border-radius: 14px; background: #fff8e8; color: #765b20; border: 1px solid #f0dfb0; }
    .reader-nav { position: fixed; right: 24px; bottom: 24px; display: flex; align-items: center; gap: 10px; padding: 10px; border: 1px solid var(--line); border-radius: 999px; background: rgba(255,255,255,0.82); backdrop-filter: blur(12px); }
    .reader-nav button { border: 1px solid var(--line); background: #fff; color: var(--ink); border-radius: 999px; padding: 8px 12px; cursor: pointer; }
    @media (max-width: 760px) {
      .reader-card { padding: 16px; align-items: start; }
      .card-shell { min-height: auto; grid-template-columns: 1fr; border-radius: 20px; }
      .card-facts { border-right: 0; border-bottom: 1px solid var(--line); }
      .card-facts, .card-details { padding: 28px; }
      .detail-grid { grid-template-columns: 1fr; }
      .reader-nav { left: 16px; right: 16px; justify-content: space-between; }
    }"""


def _javascript() -> str:
    return """    const cards = Array.from(document.querySelectorAll('[data-card]'));
    const progress = document.querySelector('[data-progress]');
    let index = 0;

    function showCard(nextIndex) {
      index = Math.max(0, Math.min(cards.length - 1, nextIndex));
      cards[index].scrollIntoView({ behavior: 'smooth', block: 'start' });
      progress.textContent = `${index + 1} / ${cards.length}`;
    }

    document.querySelector('[data-next]').addEventListener('click', () => showCard(index + 1));
    document.querySelector('[data-prev]').addEventListener('click', () => showCard(index - 1));
    document.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowRight' || event.key === 'ArrowDown' || event.key === 'PageDown') showCard(index + 1);
      if (event.key === 'ArrowLeft' || event.key === 'ArrowUp' || event.key === 'PageUp') showCard(index - 1);
      if (event.key === 'Home') showCard(0);
      if (event.key === 'End') showCard(cards.length - 1);
    });"""


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _optional(value: Any) -> str:
    if value in (None, ""):
        return "Not listed"
    return _escape(value)


def _link_or_placeholder(value: Any) -> str:
    if value in (None, ""):
        return "Not listed"
    escaped = _escape(value)
    return f'<a href="{escaped}">{escaped}</a>'


def _release_label(release: Any) -> str:
    if not isinstance(release, Mapping):
        return "No release listed"
    name = _escape(release.get("name") or release.get("tag_name") or "Release")
    url = release.get("url")
    published = release.get("published_at")
    label = name
    if url:
        label = f'<a href="{_escape(url)}">{name}</a>'
    if published:
        label += f" <span>({_escape(published)})</span>"
    return label


if __name__ == "__main__":
    raise SystemExit(main())
