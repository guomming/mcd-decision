#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
麦当劳中国 MCP 通用客户端（仅标准库，无第三方依赖）

用法:
    export MCD_MCP_TOKEN="你的token"
    python3 mcd_client.py <tool_name> ['{json args}']

示例:
    python3 mcd_client.py tools/list
    python3 mcd_client.py now-time-info '{}'
    python3 mcd_client.py query-nearby-stores '{"beType":1,"searchType":2,"city":"东莞","keyword":"东莞"}'
    python3 mcd_client.py query-meals '{"storeCode":"xxx"}'
    python3 mcd_client.py auto-bind-coupons '{}'
    python3 mcd_client.py calculate-price '{"storeCode":"xxx","items":[{"productCode":"xxx","qty":1}]}'

协议: MCP (Model Context Protocol) over Streamable HTTP, JSON-RPC 2.0
"""
import json
import os
import sys
import urllib.request

URL = os.environ.get("MCD_MCP_URL", "https://mcp.mcd.cn")
TOKEN = os.environ.get("MCD_MCP_TOKEN", "")
PROTOCOL_VERSION = "2025-06-18"

_state = {"session_id": None, "inited": False}


def _post(payload, notify=False):
    """发送一次 JSON-RPC 请求；notify=True 表示 notification（无响应体）。"""
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": "Bearer %s" % TOKEN,
    }
    if _state["session_id"]:
        headers["Mcp-Session-Id"] = _state["session_id"]

    req = urllib.request.Request(URL, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            sid = resp.headers.get("Mcp-Session-Id") or resp.headers.get("mcp-session-id")
            if sid:
                _state["session_id"] = sid
            body = resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")
        if e.code == 401:
            raise SystemExit("HTTP 401: MCP Token 无效、已过期或未提供，请到 https://open.mcd.cn/mcp 重新激活")
        if e.code == 429:
            raise SystemExit("HTTP 429: 触发限流（600 次/分钟），请降低调用频率后重试")
        raise SystemExit("HTTP %s: %s" % (e.code, detail))

    if notify or not body.strip():
        return None
    return _decode(body)


def _decode(body):
    """兼容 application/json 与 text/event-stream (SSE) 两种返回。"""
    text = body.strip()
    if text.startswith("event:") or text.startswith("data:"):
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                chunk = line[len("data:"):].strip()
                if chunk:
                    return json.loads(chunk)
        raise SystemExit("SSE 响应中未找到 data 行")
    return json.loads(text)


def initialize():
    """握手：initialize + notifications/initialized。"""
    if _state["inited"]:
        return
    _post({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "mcd-decision", "version": "1.0.0"},
        },
    })
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"}, notify=True)
    _state["inited"] = True


def list_tools():
    initialize()
    return _post({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})


def call(tool, arguments=None):
    initialize()
    return _post({
        "jsonrpc": "2.0", "id": 3, "method": "tools/call",
        "params": {"name": tool, "arguments": arguments or {}},
    })


def main():
    if not TOKEN:
        raise SystemExit("缺少 MCD_MCP_TOKEN。请先在 https://open.mcd.cn/mcp 激活并 export。")
    if len(sys.argv) < 2:
        print(__doc__)
        return

    tool = sys.argv[1]
    args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

    if tool == "tools/list":
        result = list_tools()
    else:
        result = call(tool, args)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
