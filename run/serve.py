#!/usr/bin/env python3
"""本地报告服务：在专用端口上展示 output/ 下的所有报告。

- 端口默认取 config/settings.yaml 的 server.port（8770），可用 --port 或环境变量 PORT 覆盖。
- 若端口被占用，自动向后顺延（最多 server.port_scan_limit 个），避免与其他项目抢端口。
- host 默认 0.0.0.0（同一 WiFi 下手机可访问）；用 --host 127.0.0.1 可限制为仅本机。
"""
from __future__ import annotations

import argparse
import html
import os
import socket
import sys
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from trendminer.config import Settings, load_settings  # noqa: E402


def _resolve_output_root(settings: Settings) -> Path:
    root = Path(settings.output_dir)
    return root if root.is_absolute() else PROJECT_ROOT / root


def _lan_ip() -> str:
    """获取本机在局域网中的 IP（用于手机访问提示）。"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def build_index(output_root: Path) -> str:
    rows = []
    if output_root.exists():
        run_dirs = sorted(
            (d for d in output_root.iterdir() if d.is_dir()),
            key=lambda d: d.stat().st_mtime,
            reverse=True,
        )
        for d in run_dirs:
            html_link = f'<a href="/{d.name}/report.html">报告(HTML)</a>' if (d / "report.html").exists() else ""
            md_link = f'<a href="/{d.name}/report.md">报告(MD)</a>' if (d / "report.md").exists() else ""
            stages = len(list(d.glob("stage_*.json")))
            mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(d.stat().st_mtime))
            rows.append(
                f"<tr><td>{html.escape(d.name)}</td><td>{mtime}</td>"
                f"<td>{stages}</td><td>{html_link} {md_link}</td></tr>"
            )
    body = "".join(rows) or '<tr><td colspan="4">暂无报告，先运行一次 trendminer。</td></tr>'
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>trendminer 报告服务</title>
<style>
  body{{background:#0f1115;color:#e7e9ee;font:15px/1.7 -apple-system,"PingFang SC",sans-serif;margin:0}}
  .wrap{{max-width:900px;margin:0 auto;padding:40px 20px}}
  h1{{font-size:22px;margin:0 0 4px}} .sub{{color:#9aa3b2;font-size:13px}}
  table{{width:100%;border-collapse:collapse;margin-top:20px}}
  th,td{{border:1px solid #272b34;padding:10px;text-align:left}}
  th{{background:#1e222b;color:#9aa3b2}}
  a{{color:#5b8cff;text-decoration:none;margin-right:12px}} a:hover{{text-decoration:underline}}
  .tw{{overflow-x:auto;-webkit-overflow-scrolling:touch}}
  @media (max-width:640px){{
    .wrap{{padding:20px 12px}}
    h1{{font-size:19px}}
    table{{font-size:12px;margin-top:14px}}
    th,td{{padding:8px 6px;white-space:nowrap}}
    a{{display:inline-block;margin:0 10px 4px 0}}
  }}
</style></head><body><div class="wrap">
<h1>AI时代趋势问题挖掘与变现规划 · 报告服务</h1>
<p class="sub">目录：{html.escape(str(output_root))}</p>
<div class="tw"><table><thead><tr><th>run_id</th><th>生成时间</th><th>阶段产物</th><th>报告</th></tr></thead>
<tbody>{body}</tbody></table></div>
</div></body></html>"""


class ReportHandler(SimpleHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path in ("/", "/index.html"):
            content = build_index(Path(self.directory)).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return
        return super().do_GET()

    def log_message(self, fmt, *args):  # noqa: A003
        sys.stderr.write("[trendminer] " + (fmt % args) + "\n")


def _make_server(host: str, start_port: int, scan_limit: int, handler) -> ThreadingHTTPServer:
    last_error: Exception | None = None
    for port in range(start_port, start_port + scan_limit):
        try:
            return ThreadingHTTPServer((host, port), handler)
        except OSError as exc:  # 端口被占用则顺延
            last_error = exc
    raise RuntimeError(
        f"{host} 上 {start_port}~{start_port + scan_limit - 1} 均被占用，请用 --port 指定其它端口"
    ) from last_error


def main(argv: list[str] | None = None) -> int:
    settings = load_settings()
    parser = argparse.ArgumentParser(prog="trendminer-serve", description="本地报告服务")
    parser.add_argument("--host", default=settings.server.host)
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", settings.server.port)))
    parser.add_argument("--no-scan", action="store_true", help="端口被占用时直接报错，不自动顺延")
    args = parser.parse_args(argv)

    output_root = _resolve_output_root(settings)
    output_root.mkdir(parents=True, exist_ok=True)

    scan_limit = 1 if args.no_scan else settings.server.port_scan_limit
    handler = partial(ReportHandler, directory=str(output_root))
    server = _make_server(args.host, args.port, scan_limit, handler)
    port = server.server_address[1]
    note = "" if port == args.port else f"（{args.port} 被占用，已自动顺延）"
    print(f"[trendminer] 本机访问：http://127.0.0.1:{port}/{note}", flush=True)
    if args.host == "0.0.0.0":
        print(f"[trendminer] 手机访问（同一 WiFi）：http://{_lan_ip()}:{port}/", flush=True)
    print(f"[trendminer] 服务目录：{output_root}", flush=True)
    print("[trendminer] Ctrl+C 停止", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[trendminer] 已停止")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
