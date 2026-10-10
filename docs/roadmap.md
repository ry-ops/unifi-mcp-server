# 🗺️ UniFi MCP Server roadmap

**Last updated:** October 9, 2026

## ✅ 2.0.0: cloud-only, full Network API (done)

- [x] Every call goes to `api.ui.com` with one API key; Network calls use the Site Manager cloud connector
- [x] Console and default site auto-discovered (`UNIFI_CONSOLE_ID`, `UNIFI_SITE_ID` to pin them)
- [x] One tool for each of the 73 operations in the UniFi Network API v10.6.106
- [x] One tool for each of the 9 Site Manager API v1.0.0 operations (the connector itself excluded)
- [x] Tools generated from the bundled OpenAPI specs (`scripts/generate_tools.py`), so a new API version is a regenerate
- [x] `docs/commands.md` generated from the same source
- [x] Repo tidied: docs under `docs/`, code under `unifi_mcp/`, stale generated reports removed
- [x] MCP tool annotations (read-only, destructive, idempotent) on every tool
- [x] `UNIFI_READ_ONLY=true` mode
- [x] `describe_operation` returns the full request schema; `list_operations` lists coverage
- [x] Offset and token pagination with `all_pages`
- [x] Path values encoded and checked, so IDs can't walk the proxied path; requests limited to `api.ui.com`
- [x] Logs on stderr only, so stdout stays clean for MCP ([#39](https://github.com/ry-ops/unifi-mcp-server/issues/39))
- [x] Offline test suite covering every operation, run in CI with a check that generated files match the specs
- [x] Every read endpoint verified against a live console (UDM Pro, Network 11.0.81)
- [x] Every write endpoint verified against the same console: create, update and delete cycles on test objects, and device, port, client and adoption actions sent with an unknown ID so nothing restarts

### Removed in 2.0.0

These depended on reaching the console directly, or called endpoints that aren't in the Network API:

- Local console mode (`UNIFI_GATEWAY_HOST`, `UNIFI_GATEWAY_PORT`, `UNIFI_VERIFY_TLS`)
- Classic API login with username and password, and the WLAN toggle built on it
- UniFi Protect and Access tools
- `block_client`, `unblock_client`, `kick_client`, `locate_device`
- The 26 hand-written status, host-listing and debug tools, replaced by `unifi_health`, `get_site_status`, `search_site` and the generated tools

[troubleshooting.md](troubleshooting.md#a-tool-you-expected-is-missing) maps old tools to new ones.

## 🔄 Next

- [ ] UniFi Protect API through the same cloud connector, generated from its spec
- [ ] Typed request bodies for the most-used writes (firewall policy, network, Wi-Fi) instead of a free-form `body`
- [ ] Optional local mode (direct to the console) using the same generated tools and a different base URL
- [ ] Watch developer.ui.com for a Network API newer than 10.6.106 and regenerate

## 🌟 Later

- [ ] Multi-console mode: pick the console per call instead of per server
- [ ] Change previews: show the diff between the current object and a planned `update_*` body
- [ ] Scheduled health summaries
