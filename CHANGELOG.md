# Changelog

All notable changes to this project are documented here.

This file is maintained automatically by
[release-please](https://github.com/googleapis/release-please) from
[Conventional Commits](https://www.conventionalcommits.org/). Do not edit entries
by hand — they are generated when a release PR is merged. See
[CONTRIBUTING.md](CONTRIBUTING.md) for the release flow.

## [0.1.0](https://github.com/Olaw2jr/gns3-mcp/compare/v0.1.0...v0.1.0) (2026-06-18)


### chore

* release 0.1.0 ([1555917](https://github.com/Olaw2jr/gns3-mcp/commit/1555917e3d537b3fea15dc551a4c1bd09f8d1b25))


### Documentation

* add CHANGELOG seed and Conventional Commits / release guide ([b264e6c](https://github.com/Olaw2jr/gns3-mcp/commit/b264e6ce98eab13942125d3c87a79ff077663041))

## 0.1.0

Initial release.

- MCP server for the GNS3 v3 (3.0) controller REST API (Python + FastMCP).
- ~125 tools across controller, projects, nodes, links, drawings, snapshots,
  templates, computes, images, appliances, resource pools, full RBAC
  (users/groups/roles/privileges/ACL), and packet capture.
- Telnet console automation: `node_console_send`, `node_console_session`,
  `node_console_read`, `node_console_info`.
- 4 MCP resources (projects, templates, computes, project topology) and 3 prompts
  (`build_lab`, `troubleshoot_node`, `snapshot_before_change`).
- `GNS3_READ_ONLY` mode and `confirm=true` gating on destructive operations.
- Packaged as a Claude Code plugin and a pip-installable standalone server.
