from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Asia/Taipei")


def fail(message: str) -> None:
    print(f"[validate] ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_generated_site(root: Path, report_date: str) -> None:
    docs = root / "docs"
    weekly = docs / "weekly"
    report_path = weekly / f"{report_date}.md"
    index_path = weekly / "index.md"
    homepage_path = docs / "index.md"

    for path in [report_path, index_path, homepage_path]:
        if not path.is_file():
            fail(f"missing generated file: {path.relative_to(root)}")

    index = index_path.read_text(encoding="utf-8")
    homepage = homepage_path.read_text(encoding="utf-8")
    direct_link = f"weekly/{report_date}/"

    if report_date not in index:
        fail(f"weekly index does not contain {report_date}")
    if report_date not in homepage:
        fail(f"homepage does not contain {report_date}")
    if direct_link not in homepage:
        fail(f"homepage does not contain direct report link {direct_link}")
    if f"weekly/{report_date}.md" in homepage:
        fail("homepage uses a source Markdown link instead of a generated report URL")
    if not re.search(rf"href=\"{re.escape(report_date)}/\"", index):
        fail("weekly index does not link directly to the latest report")

    first_archive = re.search(r'href="(\d{4}-\d{2}-\d{2})/"', index)
    if first_archive is None or first_archive.group(1) != report_date:
        fail("latest report is not first in the weekly archive")


def main() -> None:
    report_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now(TZ).strftime("%Y-%m-%d")
    root = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else DEFAULT_ROOT
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", report_date):
        fail(f"invalid report date: {report_date}")

    validate_generated_site(root, report_date)
    print(f"[validate] generated site contains latest report {report_date}")


if __name__ == "__main__":
    main()
