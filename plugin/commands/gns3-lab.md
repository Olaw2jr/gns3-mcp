---
description: Scaffold or modify a GNS3 lab topology from a natural-language description.
---

You are working with a GNS3 v3 controller through the `gns3` MCP server.

Goal: $ARGUMENTS

Follow this workflow:
1. Call `gns3_version` to confirm connectivity, then `templates_list` to see available
   device templates and `computes_list` for available compute servers.
2. Create a project with `project_create` and open it with `project_open` (or reuse an
   existing one from `projects_list`).
3. Add nodes with `node_create_from_template`, laying them out on the canvas with sensible
   `x`/`y` spacing. Use `node_get` to read each node's `ports`.
4. Connect ports with `link_create` (adapter_number/port_number from the ports list).
5. Start the lab with `nodes_start_all`, then verify reachability with `node_console_send`
   (e.g. configure IPs with `node_console_session`, then ping).
6. Summarize the final topology using the `gns3://project/<id>/topology` resource.

Before any risky change, take a `snapshot_create`. Confirm destructive actions explicitly.
