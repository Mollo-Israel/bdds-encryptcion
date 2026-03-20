#!/usr/bin/env python3
"""
Espera hasta que los puertos TCP estén disponibles.
Uso: python scripts/wait_ports.py host:port [host:port ...]

Retorna 0 si todos los puertos responden antes del timeout.
Retorna 1 si alguno no responde.
"""
import socket
import sys
import time


def wait_port(host: str, port: int, timeout: int = 120, interval: float = 2.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except OSError:
            time.sleep(interval)
    return False


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python wait_ports.py host:port [host:port ...]")
        sys.exit(1)

    targets = []
    for arg in sys.argv[1:]:
        host, port_str = arg.rsplit(":", 1)
        targets.append((host, int(port_str)))

    all_ok = True
    for host, port in targets:
        print(f"  Esperando {host}:{port}...", end=" ", flush=True)
        if wait_port(host, port):
            print("OK")
        else:
            print("TIMEOUT")
            all_ok = False

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
