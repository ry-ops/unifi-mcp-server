"""Offline tests: every spec operation has a tool, and each tool sends the right request.

Run with: uv run python -m unittest discover -s tests
No network access and no API key needed; HTTP is mocked.
"""
import asyncio, inspect, json, os, re, subprocess, sys, unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["UNIFI_API_KEY"] = "test-key"
os.environ["UNIFI_CONSOLE_ID"] = "CONSOLE:1"
os.environ["UNIFI_SITE_ID"] = "11111111-1111-1111-1111-111111111111"

import unifi_mcp.client as uc
import unifi_mcp.tools as unifi_tools
import main

SPECS = {
    "network": ROOT / "specs/network-v10.6.106.openapi.json",
    "cloud": ROOT / "specs/site-manager-v1.0.0.openapi.json",
}

class FakeResponse:
    status_code, reason, text = 200, "OK", '{"data": [], "count": 0, "totalCount": 0}'
    url = ""
    def json(self):
        return json.loads(self.text)

def spec_operations(api):
    spec = json.loads(SPECS[api].read_text())
    for path, item in spec["paths"].items():
        for method, op in item.items():
            if method in ("get", "post", "put", "patch", "delete") and not op["operationId"].startswith("Connector"):
                yield method.upper(), path, op

def sample_args(fn):
    args = {}
    for name, p in inspect.signature(fn).parameters.items():
        if p.default is not inspect.Parameter.empty:
            continue
        args[name] = {"body": {"example": True}}.get(name, 7 if "int" in str(p.annotation) else f"{name}-value")
    return args

class CoverageTest(unittest.TestCase):
    def test_every_spec_operation_has_one_tool(self):
        tools = {(o["api"], o["method"], o["path"]) for o in unifi_tools.OPERATIONS}
        for api in SPECS:
            for method, path, op in spec_operations(api):
                self.assertIn((api, method, path), tools, f"{op['operationId']} has no tool")
        self.assertEqual(len(tools), len(unifi_tools.OPERATIONS), "two tools share an operation")

    def test_network_operation_count(self):
        self.assertEqual(sum(o["api"] == "network" for o in unifi_tools.OPERATIONS), 73)

    def test_generated_file_is_current(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts/generate_tools.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr or r.stdout)

    def test_registered_tools_match_commands_md(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import generate_tools
        names = {t.name for t in asyncio.run(main.mcp.list_tools())}
        expected = {o["name"] for o in unifi_tools.OPERATIONS} | {n for n, _ in generate_tools.HELPERS}
        self.assertEqual(names, expected)

class RequestShapeTest(unittest.TestCase):
    def test_each_tool_sends_its_method_and_path(self):
        for op in unifi_tools.OPERATIONS:
            fn = unifi_tools.FUNCTIONS[op["name"]]
            args = sample_args(fn)
            with mock.patch.object(uc.SESSION, "request", return_value=FakeResponse()) as req:
                fn(**args)
            method, url = req.call_args.args
            kwargs = req.call_args.kwargs
            self.assertEqual(method, op["method"], op["name"])
            self.assertEqual(kwargs["headers"]["X-API-KEY"], "test-key")
            prefix = (uc.CLOUD_BASE + "/v1/connector/consoles/CONSOLE:1/proxy/network/integration"
                      if op["api"] == "network" else uc.CLOUD_BASE)
            pattern = re.escape(op["path"]).replace(r"\{siteId\}", re.escape(os.environ["UNIFI_SITE_ID"]))
            pattern = re.sub(r"\\\{\w+\\\}", r"[^/]+", pattern)
            self.assertRegex(url, "^" + re.escape(prefix) + pattern + "$", op["name"])
            self.assertEqual(kwargs["json"], args.get("body"), op["name"])

    def test_query_parameters_drop_none(self):
        with mock.patch.object(uc.SESSION, "request", return_value=FakeResponse()) as req:
            unifi_tools.list_adopted_devices(filter="state.eq('ONLINE')")
        self.assertEqual(req.call_args.kwargs["params"], {"offset": 0, "limit": 25, "filter": "state.eq('ONLINE')"})

    def test_path_traversal_rejected(self):
        for bad in ("..", "a/b", "."):
            with self.assertRaises(uc.UniFiHTTPError):
                unifi_tools.get_adopted_device_details(device_id=bad)

    def test_offset_pagination(self):
        pages = [{"offset": 0, "count": 2, "totalCount": 3, "data": [1, 2]},
                 {"offset": 2, "count": 1, "totalCount": 3, "data": [3]}]
        responses = [mock.Mock(status_code=200, text=json.dumps(p), url="", json=lambda p=p: p) for p in pages]
        with mock.patch.object(uc.SESSION, "request", side_effect=responses):
            out = unifi_tools.list_adopted_devices(limit=2, all_pages=True)
        self.assertEqual(out["data"], [1, 2, 3])

class StartupTest(unittest.TestCase):
    def test_startup_writes_nothing_to_stdout_and_survives_cp1252(self):
        # Issue #39: startup output on stdout corrupts MCP stdio and emoji crash cp1252 consoles
        env = {**os.environ, "PYTHONIOENCODING": "cp1252"}
        code = "import main; print('READY', len(main.OPERATIONS), file=__import__('sys').stderr)"
        r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr.decode("cp1252", "replace"))
        self.assertEqual(r.stdout, b"")
        self.assertIn(b"READY", r.stderr)

class SafetyTest(unittest.TestCase):
    def test_hints(self):
        ops = {o["name"]: o for o in unifi_tools.OPERATIONS}
        self.assertTrue(ops["list_adopted_devices"]["read_only"])
        self.assertTrue(ops["delete_network"]["destructive"])
        self.assertTrue(ops["execute_adopted_device_action"]["destructive"])
        self.assertTrue(ops["cloud_query_isp_metrics"]["read_only"])
        self.assertFalse(ops["create_network"]["read_only"])

    def test_requests_stay_on_api_ui_com(self):
        with self.assertRaises(uc.UniFiHTTPError):
            uc._request("GET", "https://example.com/v1/hosts")

    def test_describe_operation_inlines_body_schema(self):
        out = main.describe_operation("create_firewall_policy")
        self.assertEqual(out["method"], "POST")
        self.assertNotIn("$ref", json.dumps(out["request_body_schema"])[:200])
        self.assertIn("action", out["request_body_schema"]["properties"])

if __name__ == "__main__":
    unittest.main()
