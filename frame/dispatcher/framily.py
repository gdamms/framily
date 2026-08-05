#!/usr/bin/env python3
"""NetworkManager dispatcher hook for wlan0.

This is intentionally a thin, fast, fire-and-forget nudge - NOT where the
frame's actual logic lives. It used to run the whole registration/fetch loop
inline, which is unsupervised (nothing restarts it if it dies or never
fires) and can duplicate if NetworkManager re-fires the event while a
previous invocation is still running. That logic now lives in
framily-agent.service, a proper systemd-supervised, always-on service that
polls network state itself and does not depend on this hook firing at all.

All this script does on a wlan0 state change is touch a file the agent is
already watching, so the agent reacts a little faster than its own poll
interval would - never required for correctness.
"""
import argparse
import sys

from dotenv import load_dotenv

load_dotenv("/opt/framily/config.env")

sys.path.append("/opt/framily")

from logging_setup import get_logger
from utils import AGENT_RECHECK_PATH

logger = get_logger("dispatcher")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Framily dispatcher hook")
    parser.add_argument("interface", type=str, help="Network interface to monitor (e.g., wlan0)")
    parser.add_argument("action", type=str, help="Connection action (e.g., up, down)")
    args = parser.parse_args()

    if args.interface != "wlan0":
        sys.exit(0)

    logger.info(f"wlan0 dispatcher event: {args.action}")
    AGENT_RECHECK_PATH.touch(exist_ok=True)
