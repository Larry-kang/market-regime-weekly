# Public weekly market report site

This repository stores the public, de-identified weekly market reports that power the GitHub Pages site.

## Local preview

```bash
uvx --from mkdocs mkdocs serve
```

## Build

```bash
uvx --from mkdocs-material mkdocs build --strict
```

## Automation

A scheduled GitHub Actions workflow generates the weekly Markdown reports and refreshes the site automatically.
