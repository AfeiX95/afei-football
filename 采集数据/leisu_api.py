# -*- coding: utf-8 -*-
"""雷速体育 API 采集脚本: 构造 auth_data 签名调用 api-gateway.leisu.com"""
import hashlib
import json
import time
import uuid as uuid_mod
import urllib.request
import urllib.parse

SECRET = "uHhANonwd4UdpzOdsUqUsnl5PjurM877"
BASE = "https://api-gateway.leisu.com"
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15"


def auth_data(url_path: str, c: str) -> str:
    r = int(time.time()) + 10
    l = f"{url_path}-{r}-{c}-0-{SECRET}"
    u = hashlib.md5(l.encode()).hexdigest()
    return f"{r}-{c}-0-{u}"


def api_get(url_path: str, params: dict, c: str = ""):
    qs = urllib.parse.urlencode(params)
    url = f"{BASE}{url_path}?{qs}"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", UA)
    req.add_header("Referer", "https://m.leisu.com/")
    req.add_header("Origin", "https://m.leisu.com")
    req.add_header("auth_data", auth_data(url_path, c))
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body
    except Exception as e:
        return getattr(e, "code", "ERR"), str(e)


if __name__ == "__main__":
    # 测试不同 c 值
    for c in ["", str(uuid_mod.uuid4()), "00000000-0000-0000-0000-000000000000"]:
        st, body = api_get("/v1/web/match/common/search", {"keyword": "PAOK"}, c=c)
        print(f"c={c!r:50s} -> {st} {body[:200]}")
