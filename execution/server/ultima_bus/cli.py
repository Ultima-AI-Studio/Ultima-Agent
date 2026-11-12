"""Command line interface for the capability plugin bus."""

from __future__ import annotations

import argparse
import json
import os
from typing import Any

from .errors import BusError
from .kernel import BusKernel


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m ultima_bus")
    top = parser.add_subparsers(dest="group", required=True)
    bus = top.add_parser("bus")
    commands = bus.add_subparsers(dest="command", required=True)
    list_parser = commands.add_parser("list")
    list_parser.add_argument("domain", nargs="?")
    load = commands.add_parser("load")
    load.add_argument("module_id")
    unload = commands.add_parser("unload")
    unload.add_argument("module_id")
    switch = commands.add_parser("switch")
    switch.add_argument("module_id")
    switch.add_argument("version")
    rollback = commands.add_parser("rollback")
    rollback.add_argument("module_id")
    commands.add_parser("status")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        paths = {
            name: os.environ[value]
            for name, value in (
                ("state_path", "ULTIMA_BUS_STATE_PATH"),
                ("log_path", "ULTIMA_BUS_LOG_PATH"),
                ("ops_path", "ULTIMA_BUS_OPS_PATH"),
                ("package_root", "ULTIMA_BUS_PACKAGE_ROOT"),
            )
            if value in os.environ
        }
        with BusKernel(**paths) as kernel:
            kernel.discover()
            result: Any
            if args.command == "list":
                result = kernel.registry.list(args.domain)
            elif args.command == "load":
                result = kernel.load(args.module_id)
            elif args.command == "unload":
                result = kernel.unload(args.module_id)
            elif args.command == "switch":
                result = kernel.switch(args.module_id, args.version)
            elif args.command == "rollback":
                result = kernel.rollback(args.module_id)
            else:
                result = kernel.status()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (BusError, KeyError, ValueError) as exc:
        error = exc.as_result() if isinstance(exc, BusError) else {"ok": False, "error": str(exc)}
        print(json.dumps(error, ensure_ascii=False, indent=2))
        return 1
