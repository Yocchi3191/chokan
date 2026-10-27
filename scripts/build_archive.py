#!/usr/bin/env python3
"""issues/ の内容から index.html と archive.html を生成する。

1. issues/YYYY-MM-DD.html をすべて検査する(違反があれば何も書かずに失敗)
2. 最新号を index.html にコピーし、ヘッダーに archive.html へのリンクを足す
3. 日付降順の一覧を archive.html に書き出す

標準ライブラリのみ。リポジトリのルートから `python scripts/build_archive.py` で実行する。
"""
import re
import sys
from datetime import date
from html import escape
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ISSUES_DIR = ROOT / "issues"
ISSUE_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})\.html$")

FORBIDDEN_TAGS = {"script", "iframe", "form", "object", "embed", "link", "frame", "frameset"}
URL_ATTRS = {"src", "srcset", "poster", "data", "action", "formaction"}
EXTERNAL_CSS = re.compile(r"@import|url\(\s*['\"]?(?!data:)", re.IGNORECASE)

NAV_STYLE = "margin:0;padding:.5em 1em;font-size:.9em;border-bottom:1px solid #ccc"
NAV = f'<header style="{NAV_STYLE}"><a href="archive.html">バックナンバー</a></header>'
NOINDEX_META = '<meta name="robots" content="noindex, nofollow">'


class Checker(HTMLParser):
    """静的HTML・noindex の条件を検査し、違反を problems に溜める。"""

    def __init__(self):
        super().__init__()
        self.problems = []
        self.has_noindex = False
        self._in_style = False

    def handle_starttag(self, tag, attrs):
        attrs = {k.lower(): (v or "") for k, v in attrs}
        if tag in FORBIDDEN_TAGS:
            self.problems.append(f"<{tag}> は使えない")
        if tag == "meta" and attrs.get("name", "").lower() == "robots":
            tokens = {t.strip().lower() for t in attrs.get("content", "").split(",")}
            if {"noindex", "nofollow"} <= tokens:
                self.has_noindex = True
        for name, value in attrs.items():
            if name.startswith("on"):
                self.problems.append(f"イベントハンドラ属性 {name} は使えない")
            if name in URL_ATTRS and not value.strip().lower().startswith("data:"):
                self.problems.append(f"<{tag} {name}=...> は外部参照になるため使えない")
            if name == "style" and EXTERNAL_CSS.search(value):
                self.problems.append("style 属性内の外部参照(@import / url())は使えない")
        if tag == "style":
            self._in_style = True

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False

    def handle_data(self, data):
        if self._in_style and EXTERNAL_CSS.search(data):
            self.problems.append("<style> 内の外部参照(@import / url())は使えない")


def check_html(text):
    checker = Checker()
    checker.feed(text)
    checker.close()
    problems = list(dict.fromkeys(checker.problems))
    if not checker.has_noindex:
        problems.append(f"{NOINDEX_META} がない")
    return problems


def collect_issues():
    issues = []
    for path in ISSUES_DIR.glob("*.html"):
        m = ISSUE_NAME.match(path.name)
        if not m:
            raise SystemExit(f"issues/{path.name}: ファイル名は YYYY-MM-DD.html にする")
        try:
            day = date.fromisoformat(m.group(1))
        except ValueError:
            raise SystemExit(f"issues/{path.name}: 存在しない日付")
        issues.append((day, path))
    if not issues:
        raise SystemExit("issues/ に号がない")
    return sorted(issues, reverse=True)


def add_nav(text):
    m = re.search(r"<body[^>]*>", text, re.IGNORECASE)
    if not m:
        raise SystemExit("最新号に <body> がない")
    return text[: m.end()] + "\n" + NAV + text[m.end():]


def render_archive(issues):
    items = "\n".join(
        f'<li><a href="issues/{p.name}">{d.isoformat()}</a></li>' for d, p in issues
    )
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{NOINDEX_META}
<title>{escape("バックナンバー")}</title>
<style>body{{font-family:sans-serif;max-width:40em;margin:0 auto;padding:1em}}li{{margin:.3em 0}}</style>
</head>
<body>
<h1>バックナンバー</h1>
<ul>
{items}
</ul>
<p><a href="index.html">最新号へ</a></p>
</body>
</html>
"""


def main():
    issues = collect_issues()
    failed = False
    for _, path in issues:
        for problem in check_html(path.read_text(encoding="utf-8")):
            print(f"issues/{path.name}: {problem}", file=sys.stderr)
            failed = True
    if failed:
        return 1

    latest = issues[0][1].read_text(encoding="utf-8")
    archive = render_archive(issues)
    index = add_nav(latest)
    # 生成物自体も同じ条件を満たすこと
    for name, text in (("index.html", index), ("archive.html", archive)):
        for problem in check_html(text):
            print(f"{name}: {problem}", file=sys.stderr)
            failed = True
    if failed:
        return 1

    (ROOT / "index.html").write_text(index, encoding="utf-8", newline="\n")
    (ROOT / "archive.html").write_text(archive, encoding="utf-8", newline="\n")
    print(f"OK: {len(issues)} 号、最新 {issues[0][0].isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
