#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GitHub 同步脚本（走 REST API，规避 github.com 主域名被间歇性拦截的问题）

背景：某些网络会对 SNI=github.com 的 TLS 握手做概率性重置，导致
      git push / 网页浏览时好时坏；但 api.github.com 一直稳定可达。
      本脚本只用 api.github.com，因此对 github.com 的封锁免疫。

用法：
    set MCD_GITHUB_TOKEN=ghp_xxxx          # Windows
    python sync_github_api.py              # 正式同步
    python sync_github_api.py --dry-run    # 只看差异，不改远程

特性：
    - 内容比对：只上传真正变动的文件（用 blob SHA 判定，二进制也支持）
    - 自动重试：网络抖动自动重试 3 次
    - 路径安全：跳过 .git / __pycache__ / .pyc
    - 凭证不外泄：令牌从环境变量读取，绝不落盘
"""

import base64
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request

OWNER = "guomming"
REPO = "mcd-decision"
BRANCH = "main"
API = f"https://api.github.com/repos/{OWNER}/{REPO}"

SKIP_DIRS = {".git", "__pycache__", ".idea", ".vscode", "node_modules"}
SKIP_SUFFIX = {".pyc", ".pyo"}

TEXT_SUFFIX = {
    ".md", ".json", ".py", ".txt", ".svg", ".yml", ".yaml",
    ".gitignore", ".example", ".sh", ".cfg", ".ini",
}


def get_token():
    tok = os.environ.get("MCD_GITHUB_TOKEN", "").strip()
    if not tok:
        print("[错误] 未找到令牌。请先执行：")
        print("       set MCD_GITHUB_TOKEN=你的令牌")
        sys.exit(1)
    return tok


def request(method, url, token, payload=None, timeout=60, retries=3):
    """带重试的 HTTP 请求。"""
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    last_err = None
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(
            url, data=data, method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer " + token,
                "User-Agent": "mcd-sync-script",
                "Content-Type": "application/json; charset=utf-8",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            # 404 属于确定性结果，不必重试
            if e.code == 404:
                return {"__error__": e.code, "__body__": body[:200]}
            last_err = f"HTTP {e.code}: {body[:200]}"
        except Exception as e:
            last_err = repr(e)
        if attempt < retries:
            print(f"      重试 {attempt}/{retries - 1} ({last_err})")
            time.sleep(1.5 * attempt)
    return {"__error__": "EXC", "__body__": last_err}


def list_local_files(root):
    """遍历本地目录，返回相对路径列表。"""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if any(fn.endswith(s) for s in SKIP_SUFFIX):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace("\\", "/")
            out.append(rel)
    return sorted(out)


def blob_sha(data: bytes) -> str:
    """Git blob 对象的 SHA1：'blob <len>\\0' + content"""
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def is_text_file(rel: str, data: bytes) -> bool:
    _, ext = os.path.splitext(rel)
    if ext.lower() in TEXT_SUFFIX or os.path.basename(rel) == ".gitignore":
        return True
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def main():
    dry_run = "--dry-run" in sys.argv
    token = get_token()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    print("=" * 62)
    print("GitHub 同步（REST API 通道 · 对 github.com 封锁免疫）")
    print(f"仓库  : {OWNER}/{REPO}@{BRANCH}")
    print(f"目录  : {root}")
    print(f"模式  : {'预演（不改动远程）' if dry_run else '正式同步'}")
    print("=" * 62)

    # 1. 拉取远程当前树
    tree = request("GET", f"{API}/git/trees/{BRANCH}?recursive=1", token)
    if "__error__" in tree:
        print(f"[失败] 无法读取远程目录树：{tree.get('__body__')}")
        sys.exit(1)

    remote = {item["path"]: item for item in tree.get("tree", []) if item["type"] == "blob"}
    print(f"\n远程现有文件：{len(remote)} 个\n")

    local_files = list_local_files(root)
    print(f"本地待处理文件：{len(local_files)} 个\n")

    to_create, to_update, unchanged = [], [], []

    for rel in local_files:
        path = os.path.join(root, rel.replace("/", os.sep))
        try:
            data = open(path, "rb").read()
        except Exception as e:
            print(f"  [跳过] {rel}（读取失败：{e}）")
            continue

        local_sha = blob_sha(data)
        item = remote.get(rel)
        if item is None:
            to_create.append((rel, data))
        elif item.get("sha") != local_sha:
            to_update.append((rel, data, item["sha"]))
        else:
            unchanged.append(rel)

    print("-" * 62)
    print(f"需新建 {len(to_create)} 个 | 需更新 {len(to_update)} 个 | 无变化 {len(unchanged)} 个")
    print("-" * 62)
    for rel, _ in to_create:
        print(f"  [新建] {rel}")
    for rel, _, _ in to_update:
        print(f"  [更新] {rel}")

    if dry_run:
        print("\n预演结束，未改动远程。去掉 --dry-run 即可正式同步。")
        return

    if not to_create and not to_update:
        print("\n远程已是最新，无需同步。")
        return

    print("")

    def upload(rel, data, sha=None):
        text = is_text_file(rel, data)
        content_b64 = base64.b64encode(data).decode("ascii")
        payload = {
            "message": f"{'chore' if sha else 'feat'}: sync {rel} via REST API",
            "content": content_b64,
            "branch": BRANCH,
        }
        if sha:
            payload["sha"] = sha
        res = request("PUT", f"{API}/contents/{rel}", token, payload, timeout=120)
        if "__error__" in res:
            kind = "文本" if text else "二进制"
            print(f"  [失败] {rel}（{kind}）-> {res.get('__body__')}")
            return False
        kind = "文本" if text else "二进制"
        print(f"  [成功] {rel}（{kind}，{len(data)} 字节）")
        return True

    ok = fail = 0
    for rel, data in to_create:
        if upload(rel, data):
            ok += 1
        else:
            fail += 1
    for rel, data, sha in to_update:
        if upload(rel, data, sha):
            ok += 1
        else:
            fail += 1

    print("")
    print("=" * 62)
    print(f"同步完成：成功 {ok} 个，失败 {fail} 个")
    print(f"仓库地址：https://github.com/{OWNER}/{REPO}")
    print("=" * 62)


if __name__ == "__main__":
    main()
