# Contributing

Thanks for helping improve `gns3-mcp`. This project uses automated versioning and
releases, so a little commit hygiene goes a long way.

## Development setup

```bash
pip install -e ".[dev]"
python -m pytest -q          # hermetic unit + tool + console tests (respx-mocked)
```

Optional live smoke test against a real GNS3 v3 controller:

```bash
GNS3_LIVE=1 GNS3_BASE_URL=http://localhost:3080 \
  GNS3_USERNAME=admin GNS3_PASSWORD=... python -m pytest tests/test_live_smoke.py -s
```

Architecture in brief: a single async `GNS3Client` (`src/gns3_mcp/client.py`) handles
login, 401 re-auth, pagination, and binary I/O; each module under `src/gns3_mcp/tools/`
is a thin layer over it and exposes `register(mcp)`. `console.py` is a minimal telnet
proxy for driving node consoles. New tools go in the relevant `tools/*.py` module and are
registered from `server.py`; gate any mutating tool behind the `read_only()` check.

## Conventional Commits

Commit messages **must** follow [Conventional Commits](https://www.conventionalcommits.org/).
This is what drives automatic version bumps and the changelog.

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Common types and their release effect:

| Commit | Example | Version bump |
| --- | --- | --- |
| `feat:` | `feat: add symbol management tools` | minor (0.1.0 → 0.2.0) |
| `fix:` | `fix: handle empty console output` | patch (0.1.0 → 0.1.1) |
| `perf:` | `perf: stream large pcap downloads` | patch |
| `docs:` / `refactor:` / `test:` / `chore:` / `ci:` | `docs: clarify auth env vars` | none (shown in changelog where configured) |
| breaking | `feat!: rename node_console_send args` or a `BREAKING CHANGE:` footer | major (0.1.0 → 1.0.0) |

Scopes are optional but encouraged, e.g. `feat(nodes): ...`, `fix(client): ...`.

## Release flow (automated)

Releases are handled by [release-please](https://github.com/googleapis/release-please) —
no manual version edits.

1. Merge Conventional-Commit PRs into `master`.
2. release-please opens/updates a **`chore(main): release x.y.z`** PR that bumps the
   version (in `pyproject.toml` and `src/gns3_mcp/__init__.py`) and updates
   `CHANGELOG.md`.
3. Merge that release PR. release-please creates a GitHub Release and a `vX.Y.Z` tag.
4. The tag/release triggers the publish pipeline (`.github/workflows/publish.yml`):
   **test → build → publish to PyPI** via Trusted Publishing. Publishing only proceeds
   if the full test suite passes.

You never edit `CHANGELOG.md` or the version strings by hand — release-please owns them.
