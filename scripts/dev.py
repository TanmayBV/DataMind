#!/usr/bin/env python3
"""
scripts/dev.py
--------------
Unified Concurrent Development Server Runner for DataMind NL2SQL.
Starts both the FastAPI REST backend and Vite React frontend concurrently
with graceful signal trapping (SIGINT / Ctrl+C) and automatic teardown.

Usage:
    python scripts/dev.py
"""

import os
import signal
import subprocess
import sys
import time

BACKEND_PORT = 8000
FRONTEND_PORT = 5173

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")


def main():
    print("=" * 70)
    print(" 🧠 DataMind Universal NL2SQL — Concurrent Dev Environment")
    print("=" * 70)
    print(f" [*] Backend REST API:  http://localhost:{BACKEND_PORT}")
    print(f" [*] Interactive UI:    http://localhost:{FRONTEND_PORT}")
    print(f" [*] API Documentation: http://localhost:{BACKEND_PORT}/docs")
    print("=" * 70)
    print(" Starting development servers (Press Ctrl+C to terminate both)...")
    print()

    backend_proc = None
    frontend_proc = None

    # Determine npm executable name based on OS
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"

    # Threat T-ui-12 Mitigation: Clean signal handler ensuring child processes are killed
    def shutdown_processes(signum=None, frame=None):
        print("\n [!] Stopping development servers...")
        for name, proc in [("Frontend (Vite)", frontend_proc), ("Backend (FastAPI)", backend_proc)]:
            if proc and proc.poll() is None:
                try:
                    if sys.platform == "win32":
                        # Terminate Windows process tree
                        subprocess.run(
                            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            check=False,
                        )
                    else:
                        proc.terminate()
                        proc.wait(timeout=3)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                print(f" [-] {name} terminated.")
        print(" [✓] All DataMind processes stopped cleanly. Goodbye!\n")
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, shutdown_processes)
    signal.signal(signal.SIGTERM, shutdown_processes)

    try:
        # 1. Launch FastAPI Backend
        backend_args = [
            sys.executable,
            "-m",
            "uvicorn",
            "query_engine.api_server:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(BACKEND_PORT),
            "--reload",
        ]
        backend_proc = subprocess.Popen(
            backend_args,
            cwd=ROOT_DIR,
        )

        # 2. Launch Vite Frontend
        frontend_args = [
            npm_cmd,
            "run",
            "dev",
            "--",
            "--port",
            str(FRONTEND_PORT),
        ]
        frontend_proc = subprocess.Popen(
            frontend_args,
            cwd=FRONTEND_DIR,
            shell=(sys.platform == "win32"),
        )

        # Monitor both processes
        while True:
            time.sleep(0.5)
            if backend_proc.poll() is not None:
                print(f"\n [!] Backend exited unexpectedly with code {backend_proc.returncode}")
                break
            if frontend_proc.poll() is not None:
                print(f"\n [!] Frontend exited unexpectedly with code {frontend_proc.returncode}")
                break

    except KeyboardInterrupt:
        pass
    finally:
        shutdown_processes()


if __name__ == "__main__":
    main()
