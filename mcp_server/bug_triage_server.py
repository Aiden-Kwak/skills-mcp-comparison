"""
MCP server exposing domain-specific bug triage tools over stdio JSON-RPC.

Implements MCP protocol minimum surface (initialize, tools/list, tools/call)
without external dependencies - portable to any Python 3.10+.
"""
import json
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "bugs.db"

# === Tool definitions exposed to the client ===
TOOLS = [
    {
        "name": "list_bugs",
        "description": "List bugs with optional filters. Use for browsing recent or filtered bugs. Returns id, title, severity, status, component, reporter_type, customer_tier, created_at.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["open", "in_progress", "resolved", "closed"]},
                "severity": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
                "component": {"type": "string"},
                "since_days": {"type": "integer", "description": "Only bugs created within last N days"},
                "limit": {"type": "integer", "default": 50},
            },
        },
    },
    {
        "name": "get_bug",
        "description": "Get full detail of a single bug by id, including the full description text needed for triage decisions.",
        "inputSchema": {
            "type": "object",
            "properties": {"bug_id": {"type": "integer"}},
            "required": ["bug_id"],
        },
    },
    {
        "name": "search_bugs",
        "description": "Full-text search across bug titles and descriptions. Use to find duplicates or related bugs by keyword.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_stats",
        "description": "Aggregate counts by status, severity, and component over a recent window. Use for high-level health overview.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "since_days": {"type": "integer", "default": 7},
            },
        },
    },
]


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def tool_list_bugs(args: dict) -> str:
    conn = _conn()
    where = []
    params = []
    if args.get("status"):
        where.append("status = ?")
        params.append(args["status"])
    if args.get("severity"):
        where.append("severity = ?")
        params.append(args["severity"])
    if args.get("component"):
        where.append("component = ?")
        params.append(args["component"])
    if args.get("since_days") is not None:
        cutoff = (datetime(2026, 5, 8, 14, 0, 0) - timedelta(days=args["since_days"])).isoformat()
        where.append("created_at >= ?")
        params.append(cutoff)
    sql = "SELECT id, title, severity, status, component, reporter_type, customer_tier, created_at FROM bugs"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(args.get("limit", 50))
    rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    conn.close()
    return json.dumps(rows, ensure_ascii=False, indent=2)


def tool_get_bug(args: dict) -> str:
    conn = _conn()
    row = conn.execute("SELECT * FROM bugs WHERE id = ?", (args["bug_id"],)).fetchone()
    conn.close()
    if not row:
        return json.dumps({"error": f"bug {args['bug_id']} not found"})
    return json.dumps(dict(row), ensure_ascii=False, indent=2)


def tool_search_bugs(args: dict) -> str:
    conn = _conn()
    query = f"%{args['query']}%"
    rows = conn.execute(
        "SELECT id, title, description, severity, status, component, customer_tier, created_at "
        "FROM bugs WHERE title LIKE ? OR description LIKE ? "
        "ORDER BY created_at DESC LIMIT ?",
        (query, query, args.get("limit", 20)),
    ).fetchall()
    conn.close()
    return json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2)


def tool_get_stats(args: dict) -> str:
    conn = _conn()
    since_days = args.get("since_days", 7)
    cutoff = (datetime(2026, 5, 8, 14, 0, 0) - timedelta(days=since_days)).isoformat()
    out = {"window_days": since_days}
    out["by_severity"] = {
        r["severity"]: r["c"]
        for r in conn.execute("SELECT severity, COUNT(*) c FROM bugs WHERE created_at >= ? GROUP BY severity", (cutoff,)).fetchall()
    }
    out["by_status"] = {
        r["status"]: r["c"]
        for r in conn.execute("SELECT status, COUNT(*) c FROM bugs WHERE created_at >= ? GROUP BY status", (cutoff,)).fetchall()
    }
    out["by_component"] = {
        r["component"]: r["c"]
        for r in conn.execute("SELECT component, COUNT(*) c FROM bugs WHERE created_at >= ? GROUP BY component", (cutoff,)).fetchall()
    }
    out["total_in_window"] = sum(out["by_severity"].values())
    conn.close()
    return json.dumps(out, ensure_ascii=False, indent=2)


TOOL_HANDLERS = {
    "list_bugs": tool_list_bugs,
    "get_bug": tool_get_bug,
    "search_bugs": tool_search_bugs,
    "get_stats": tool_get_stats,
}


# === MCP JSON-RPC over stdio ===

def write(msg: dict) -> None:
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def handle(req: dict) -> dict | None:
    method = req.get("method")
    rid = req.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": rid,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "bug-triage-server", "version": "1.0.0"},
            },
        }
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = req["params"]["name"]
        args = req["params"].get("arguments", {})
        handler = TOOL_HANDLERS.get(name)
        if not handler:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"unknown tool: {name}"}}
        try:
            text = handler(args)
            return {"jsonrpc": "2.0", "id": rid, "result": {"content": [{"type": "text", "text": text}]}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32000, "message": str(e)}}
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"unknown method: {method}"}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle(req)
        if resp is not None:
            write(resp)


if __name__ == "__main__":
    main()
