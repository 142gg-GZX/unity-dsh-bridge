#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DeepSeek Harness -> Unity 桥接客户端(最小验证版),仅依赖标准库。

用法:
  python unity_client.py ping
  python unity_client.py hierarchy
  python unity_client.py create_primitive '{"type":"sphere","name":"Ball","position":[0,2,0]}'
  python unity_client.py file 'Temp/DshBridge/shot_000.png' --out shot.png

也可作为库:
  import unity_client as u
  u.call("create_primitive", {"type":"cube"})
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

BASE = os.environ.get("DSH_UNITY_BASE", "http://127.0.0.1:8790")


def _request(path, payload=None, timeout=120):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def call(method, params=None, timeout=120):
    raw = _request("/api", {"method": method, "params": params or {}}, timeout)
    res = json.loads(raw.decode("utf-8"))
    if not res.get("ok"):
        raise RuntimeError("unity bridge error [%s]: %s" % (method, res.get("error")))
    return res.get("result")


def try_call(method, params=None, timeout=120):
    """出错不抛异常,返回 {'__error__': ...}"""
    try:
        return call(method, params, timeout)
    except Exception as e:
        return {"__error__": str(e)}


def status(timeout=10):
    raw = _request("/status", None, timeout)
    return json.loads(raw.decode("utf-8"))


def set_status(text, timeout=10):
    return try_call("set_status", {"text": text}, timeout)


def ping(timeout=10):
    raw = _request("/ping", None, timeout)
    return json.loads(raw.decode("utf-8"))


def ping_until(timeout=900, interval=5, verbose=True):
    """等待 Unity 与桥接服务就绪(域重载期间会自动重试)"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            info = ping(interval)
            if info.get("ok") and not info.get("changing"):
                return info
        except Exception as e:
            info = {"__error__": str(e)}
        if verbose:
            print("  [wait] unity not ready:", json.dumps(info, ensure_ascii=False)[:160], flush=True)
        time.sleep(interval)
    raise TimeoutError("unity bridge not reachable within %ss" % timeout)


def wait_compile_idle(timeout=300, interval=3, verbose=True):
    """等待编译完成(期间服务可能因域重载重启,自动重试)"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            info = ping(interval + 5)
            if info.get("ok") and not info.get("compiling"):
                return info
            if verbose:
                print("  [wait] compiling...", flush=True)
        except Exception as e:
            if verbose:
                print("  [wait] server down (reloading?):", str(e)[:120], flush=True)
        time.sleep(interval)
    raise TimeoutError("still compiling after %ss" % timeout)


def get_file(rel_path, out_path):
    q = urllib.parse.quote(rel_path, safe="/")
    raw = _request("/file?path=" + q, None, 60)
    with open(out_path, "wb") as f:
        f.write(raw)
    return out_path


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    cmd = argv[0]
    if cmd == "ping":
        print(json.dumps(ping(), ensure_ascii=False, indent=2))
        return 0
    if cmd == "file":
        rel = argv[1] if len(argv) > 1 else ""
        out = "downloaded_" + os.path.basename(rel)
        if "--out" in argv:
            out = argv[argv.index("--out") + 1]
        get_file(rel, out)
        print("saved:", out)
        return 0
    params = json.loads(argv[1]) if len(argv) > 1 else {}
    print(json.dumps(call(cmd, params), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
