# gns3-mcp

A full-feature [MCP](https://modelcontextprotocol.io) server for the **GNS3 v3 (3.0)**
controller REST API. It lets an AI agent (Claude Code / Claude Desktop / any MCP client)
drive a GNS3 network-emulation lab end-to-end: build topologies, manage device lifecycle,
snapshot, capture packets, manage templates / computes / images / RBAC, **and automate
device CLIs over node consoles**.

Built with **Python + FastMCP**. Ships as a **Claude Code plugin** and as a standalone
pip-installable MCP server. ~125 tools, 4 resources, and 3 prompts.

## Features

| Area | Tools |
| --- | --- |
| Controller | version, statistics, reload/shutdown, IOU license |
| Projects | CRUD, open/close/load, duplicate, export/import, lock, files |
| Nodes | CRUD, create-from-template, start/stop/suspend/reload (single + all), isolate, duplicate, idle-PC, disk/files |
| Links | CRUD, filters, reset |
| Console automation | `node_console_send`, `node_console_session`, `node_console_read`, `node_console_info` (telnet) |
| Packet capture | start/stop, Wireshark restart, pcap download |
| Snapshots | list / create / restore / delete |
| Drawings | canvas annotations CRUD |
| Templates / Appliances | CRUD + duplicate; browse & install appliance catalog |
| Computes / Images | manage compute servers, query emulators; upload/install/prune images |
| RBAC | users, groups, roles, privileges, ACL |
| Resource pools | CRUD + membership |
| Resources | `gns3://projects`, `gns3://templates`, `gns3://computes`, `gns3://project/{id}/topology` |
| Prompts | `build_lab`, `troubleshoot_node`, `snapshot_before_change` |

## Configuration

All settings come from the environment (prefix `GNS3_`):

| Variable | Default | Purpose |
| --- | --- | --- |
| `GNS3_BASE_URL` | `http://localhost:3080` | Controller URL (no `/v3`) |
| `GNS3_USERNAME` / `GNS3_PASSWORD` | – | Login credentials |
| `GNS3_TOKEN` | – | Pre-issued bearer token (skips login) |
| `GNS3_VERIFY_TLS` | `true` | Verify TLS for https |
| `GNS3_DEFAULT_PROJECT` | – | Project id used when a tool omits `project_id` |
| `GNS3_READ_ONLY` | `false` | Disable all mutating tools (41 read-only tools remain) |
| `GNS3_TRANSPORT` | `stdio` | `stdio` or `http` |
| `GNS3_HTTP_HOST` / `GNS3_HTTP_PORT` | `127.0.0.1` / `8080` | HTTP bind |
| `GNS3_CONSOLE_TIMEOUT` | `15` | Console read timeout (s) |

## Install

### As a Claude Code plugin

```
/plugin marketplace add /home/oscar/Code/gns3-mcp
/plugin install gns3
```

The plugin declares the MCP server in `plugin/.mcp.json`; it runs the `gns3-mcp` console
script, so install the package first (below) or adjust the command to `python -m gns3_mcp`.

### As a standalone MCP server

```bash
pip install -e .            # from this repo (or: pipx install gns3-mcp once published)
```

Register with Claude Code:

```bash
claude mcp add gns3 -- gns3-mcp
# then set env: GNS3_BASE_URL, GNS3_USERNAME, GNS3_PASSWORD
```

Or in Claude Desktop config:

```json
{
  "mcpServers": {
    "gns3": {
      "command": "gns3-mcp",
      "env": {
        "GNS3_BASE_URL": "http://localhost:3080",
        "GNS3_USERNAME": "admin",
        "GNS3_PASSWORD": "your-password"
      }
    }
  }
}
```

Run as a remote HTTP server instead:

```bash
GNS3_TRANSPORT=http GNS3_HTTP_PORT=8080 gns3-mcp
```

## Safety

- `GNS3_READ_ONLY=true` registers only read-only tools.
- Destructive tools (`project_delete`, `node_delete` via flow, `controller_shutdown`,
  `controller_reload`, `images_prune`) require an explicit `confirm=true`.
- Console automation can run **arbitrary commands** on emulated devices — treat it like
  shell access to your lab.

## Development

```bash
pip install -e ".[dev]"
python -m pytest                 # hermetic unit + tool + console tests (respx-mocked)

# Opt-in live smoke test against a real controller:
GNS3_LIVE=1 GNS3_BASE_URL=http://localhost:3080 \
  GNS3_USERNAME=admin GNS3_PASSWORD=... python -m pytest tests/test_live_smoke.py -s
```

Architecture: a single async `GNS3Client` (`client.py`) handles login, 401 re-auth,
pagination, and binary I/O; every tool module under `tools/` is a thin layer over it and
exposes `register(mcp)`. `console.py` is a minimal telnet proxy for driving node consoles.

## Contributing & releases

Commits follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`,
`fix:`, `feat!:` for breaking changes), which drives automated versioning.
[release-please](https://github.com/googleapis/release-please) opens a release PR that
bumps the version and updates [`CHANGELOG.md`](CHANGELOG.md); merging it tags a release and
publishes to PyPI via Trusted Publishing (after the test suite passes). Full details in
[CONTRIBUTING.md](CONTRIBUTING.md).
