"""Choose a free loopback port for the Windows launch script."""

from __future__ import annotations

import socket
import sys
from pathlib import Path


def _available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: select_available_port.py <port> <explicit:0|1> <output-file>")
        return 2
    requested = int(sys.argv[1])
    explicit = sys.argv[2] == "1"
    output = Path(sys.argv[3])
    candidates = [requested] if explicit else range(requested, min(requested + 20, 65536))
    port = next((candidate for candidate in candidates if _available(candidate)), None)
    if port is None:
        if explicit:
            print(f"[ERROR] 端口 {requested} 正在使用，请关闭占用进程或指定其他端口。")
        else:
            print(f"[ERROR] 从端口 {requested} 起未找到可用端口。")
        return 1
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(str(port), encoding="ascii")
    if port != requested:
        print(f"[WARN] 端口 {requested} 已被占用，改用 {port}。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
