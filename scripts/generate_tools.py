#!/usr/bin/env python3
"""Generate unifi_mcp/tools.py from the bundled OpenAPI specs.

One MCP tool per API operation, so the server covers every call in the spec.
Re-run after dropping a new spec into specs/ (and updating SPECS below):

    python3 scripts/generate_tools.py
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "unifi_mcp" / "tools.py"
COMMANDS = ROOT / "docs" / "commands.md"

# Hand-written tools in main.py, listed first in commands.md
HELPERS = [
    ("unifi_health", "Check the API key, console, Network application version and default site."),
    ("get_site_status", "Device states, offline devices, pending firmware and clients by type, in one call."),
    ("search_site", "Find clients and devices by part of a name, MAC or IP."),
    ("list_operations", "Every API operation this server covers, optionally for one group."),
    ("describe_operation", "Full request-body schema for an API tool, before a create or update."),
]

# (api, spec file, docs base, tool-name prefix, operations to skip)
SPECS = [
    ("network", "specs/network-v10.6.106.openapi.json", "https://developer.ui.com/network/v10.6.106", "", set()),
    # The connector operations are the transport the Network tools already use
    ("cloud", "specs/site-manager-v1.0.0.openapi.json", "https://developer.ui.com/site-manager/v1.0.0", "cloud_",
     {"ConnectorGet", "ConnectorPost", "ConnectorPut", "ConnectorPatch", "ConnectorDelete"}),
]

# POSTs that only read data
READ_ONLY_POSTS = {"queryISPMetrics"}
# POSTs that change running state (restart, power-cycle, guest access)
DESTRUCTIVE_POSTS = {"executeAdoptedDeviceAction", "executePortAction", "executeConnectedClientAction"}

FILTER_HELP = ("Filter expression, e.g. name.like('U*'), state.eq('ONLINE'), "
               "and(type.eq('WIRED'),name.like('pve*')). Combine with and(), or(), not(); "
               "the fields and functions each endpoint allows are listed in its description.")

PARAM_HELP = {
    "siteId": "Site ID (UUID). Leave empty to use the default site.",
    "offset": "Number of items to skip.",
    "limit": "Page size.",
    "filter": FILTER_HELP,
    "force": "Delete even if other objects still reference it.",
    "pageSize": "Page size.",
    "nextToken": "Token from the previous page.",
    "hostIds[]": "Only these console (host) IDs.",
}

def clean(text: str) -> str:
    """Spec descriptions carry HTML (<details>, <br/>); keep the text and tables."""
    text = re.sub(r"<br\s*/?>", " ", text)
    text = re.sub(r"</?(details|summary)>", " ", text)
    text = text.replace("Filterable properties (click to expand)", "Filterable properties:")
    return " ".join(text.split())

def snake(name: str) -> str:
    name = name.replace("[]", "")
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name).lower()

def tool_name(summary: str) -> str:
    words = re.sub(r"[^A-Za-z0-9]+", " ", summary).strip().lower().split()
    return "_".join(words)

def py_type(schema: dict) -> str:
    t = schema.get("type")
    if t == "integer":
        return "int"
    if t == "boolean":
        return "bool"
    if t == "array":
        return "List[str]"
    return "str"

def resolve(spec: dict, schema: dict) -> dict:
    while "$ref" in schema:
        schema = spec["components"]["schemas"][schema["$ref"].split("/")[-1]]
    return schema

def props_of(spec: dict, schema: dict) -> tuple:
    """Merged (properties, required) of an object schema, following allOf."""
    schema = resolve(spec, schema)
    props, required = dict(schema.get("properties", {})), set(schema.get("required", []))
    for part in schema.get("allOf", []):
        p, r = props_of(spec, part)
        props.update(p)
        required |= r
    return props, required

def describe_prop(spec: dict, schema: dict) -> str:
    schema = resolve(spec, schema)
    if "enum" in schema:
        return "|".join(map(str, schema["enum"][:8]))
    if "discriminator" in schema:
        return "one of " + "|".join(schema["discriminator"].get("mapping", {}))
    t = schema.get("type") or ("object" if "properties" in schema or "allOf" in schema else "any")
    if t == "array":
        return f"array of {describe_prop(spec, schema.get('items', {}))}"
    return t

def body_outline(spec: dict, schema: dict, indent: str = "    ") -> list:
    """Short, human-readable outline of a request body for the tool description."""
    schema = resolve(spec, schema)
    lines = []
    disc = schema.get("discriminator")
    if disc:
        lines.append(f"{indent}Set `{disc['propertyName']}` to pick a variant:")
        for key, ref in disc.get("mapping", {}).items():
            props, req = props_of(spec, {"$ref": ref})
            fields = [f"{n}{'*' if n in req else ''}" for n in props if n != disc["propertyName"]]
            lines.append(f"{indent}  {key}" + (f": {', '.join(fields)}" if fields else ""))
        return lines
    props, req = props_of(spec, schema)
    for n, p in props.items():
        desc = (resolve(spec, p).get("description") or "").split("\n")[0][:70]
        lines.append(f"{indent}{n}{'*' if n in req else ''} ({describe_prop(spec, p)})" + (f": {desc}" if desc else ""))
    return lines

def operations():
    for api, spec_file, docs, prefix, skip in SPECS:
        spec = json.loads((ROOT / spec_file).read_text())
        for path, item in spec["paths"].items():
            for method, op in item.items():
                if method not in ("get", "post", "put", "patch", "delete") or op.get("operationId") in skip:
                    continue
                yield api, spec, spec_file, docs, prefix, path, method.upper(), op

def hints(method: str, op_id: str) -> dict:
    read_only = method == "GET" or op_id in READ_ONLY_POSTS
    destructive = method in ("PUT", "PATCH", "DELETE") or op_id in DESTRUCTIVE_POSTS
    idempotent = method in ("GET", "PUT", "DELETE") or read_only
    return {"read_only": read_only, "destructive": destructive and not read_only, "idempotent": idempotent}

def render() -> str:
    out = [
        "# unifi_mcp/tools.py",
        "# GENERATED by scripts/generate_tools.py from the specs in specs/. Do not edit by hand.",
        "# One function per API operation; main.py registers them as MCP tools.",
        "",
        "from typing import Annotated, Any, Dict, List, Optional",
        "from pydantic import Field",
        "from unifi_mcp.client import cloud_call, network_call",
        "",
    ]
    registry = []
    names = set()
    for api, spec, spec_file, docs, prefix, path, method, op in operations():
        op_id = op["operationId"]
        name = prefix + tool_name(op["summary"])
        if name in names:
            sys.exit(f"duplicate tool name {name} ({op_id})")
        names.add(name)

        params = op.get("parameters", [])
        required, optional = [], []
        path_args, query_args = [], []
        for p in params:
            pname, schema = p["name"], p.get("schema", {})
            arg = snake(pname)
            if pname == "filter":
                ptype = "str"
            else:
                ptype = py_type(resolve(spec, schema))
            help_text = PARAM_HELP.get(pname) or (p.get("description") or "").strip() or f"{pname} ({schema.get('format') or schema.get('type', 'string')})"
            if pname == "limit" and "maximum" in schema:
                help_text = f"Page size (max {schema['maximum']})."
            ann = f"Annotated[{ptype}, Field(description={help_text!r})]"
            (path_args if p["in"] == "path" else query_args).append((pname, arg))
            if p.get("required") and pname != "siteId":
                required.append(f"{arg}: {ann}")
            elif pname == "siteId":
                optional.insert(0, f"{arg}: Annotated[Optional[str], Field(description={help_text!r})] = None")
            else:
                default = schema.get("default")
                optional.append(f"{arg}: Annotated[Optional[{ptype}], Field(description={help_text!r})] = {default!r}")

        body_ref = None
        body_schema = (op.get("requestBody") or {}).get("content", {}).get("application/json", {}).get("schema")
        if body_schema is not None:
            body_ref = body_schema.get("$ref")
            required.append("body: Annotated[Dict[str, Any], Field(description='JSON request body. "
                            "Fields are listed in the tool description; describe_operation returns the full schema.')]")
        paged = method == "GET" and any(a in ("offset", "nextToken") for a, _ in query_args)
        if paged:
            optional.append("all_pages: Annotated[bool, Field(description='Fetch every page and return them together.')] = False")

        h = hints(method, op_id)
        doc = [op["summary"].rstrip(".") + "."]
        if op.get("description"):
            doc.append(clean(op["description"]))
        doc.append(f"{method} {path}")
        if body_schema is not None:
            doc.append("Body fields (* = required):")
            doc.extend(body_outline(spec, body_schema))
        doc.append(f"Docs: {docs}/{op_id.lower()}")

        call = "network_call" if api == "network" else "cloud_call"
        path_dict = ", ".join(f"{n!r}: {a}" for n, a in path_args)
        query_dict = ", ".join(f"{n!r}: {a}" for n, a in query_args)
        out.append(f"def {name}({', '.join(required + optional)}) -> Any:")
        out.append('    """' + "\n    ".join(line.replace('"""', "'''").replace("\\", "\\\\") for line in doc) + '\n    """')
        out.append(f"    return {call}({method!r}, {path!r}, {{{path_dict}}}, {{{query_dict}}}"
                   + (", body" if body_schema is not None else "")
                   + (", all_pages=all_pages" if paged else "") + ")")
        out.append("")
        registry.append({
            "name": name, "api": api, "method": method, "path": path, "operation_id": op_id,
            "summary": op["summary"], "tag": (op.get("tags") or [""])[0], "spec": spec_file,
            "body_schema": body_ref, **h,
        })

    out.append("OPERATIONS: List[Dict[str, Any]] = [")
    for r in registry:
        out.append(f"    {r!r},")
    out.append("]")
    out.append("")
    out.append("FUNCTIONS = {op['name']: globals()[op['name']] for op in OPERATIONS}")
    out.append("")
    return "\n".join(out), registry

def render_commands(registry: list) -> str:
    out = [
        "# UniFi MCP Server: command reference",
        "",
        "<!-- GENERATED by scripts/generate_tools.py. Do not edit by hand. -->",
        "",
        f"{len(HELPERS) + len(registry)} tools: {len(HELPERS)} helpers plus one tool for every operation in the "
        "UniFi Network API v10.6.106 and the Site Manager API v1.0.0. "
        "**Changes** means the tool can change your network; with `UNIFI_READ_ONLY=true` those tools are not registered.",
        "",
        "## Helpers",
        "",
        "| Tool | What it does |",
        "|---|---|",
    ]
    out += [f"| `{n}` | {d} |" for n, d in HELPERS]
    for api, title in (("network", "Network API (through the cloud connector)"), ("cloud", "Site Manager API (api.ui.com)")):
        ops = [r for r in registry if r["api"] == api]
        out += ["", f"## {title}", ""]
        for tag in dict.fromkeys(r["tag"] for r in ops):
            out += [f"### {tag}", "", "| Tool | Call | Changes |", "|---|---|---|"]
            for r in (r for r in ops if r["tag"] == tag):
                change = "no" if r["read_only"] else ("**yes**" if r["destructive"] else "yes")
                out.append(f"| `{r['name']}` | `{r['method']} {r['path']}` | {change} |")
            out.append("")
    out += ["", "**yes** in bold: deletes, replaces, restarts or otherwise disrupts something.", ""]
    return "\n".join(out)

if __name__ == "__main__":
    text, registry = render()
    outputs = {OUT: text, COMMANDS: render_commands(registry)}
    if "--check" in sys.argv:
        stale = [p.name for p, t in outputs.items() if not p.exists() or p.read_text() != t]
        if stale:
            sys.exit(f"out of date: {', '.join(stale)}; run python3 scripts/generate_tools.py")
        print("generated files are up to date")
    else:
        for p, t in outputs.items():
            p.write_text(t)
            print(f"wrote {p.relative_to(ROOT)}")
