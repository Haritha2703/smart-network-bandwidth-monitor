#!/usr/bin/env python3
"""Smart Network Bandwidth Monitoring and Alert System - entry point."""
import argparse
import os
import sys
import time
from collections import deque
from datetime import datetime

from src import calculator as calc
from src import display
from src.config import ConfigError, load_config
from src.interfaces import (InterfaceError, list_interfaces, read_counters,
                            select_interface)
from src.logger import MonitorLogger

ROOT = os.path.dirname(os.path.abspath(__file__))


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_args():
    p = argparse.ArgumentParser(description="Real-time network bandwidth monitor with alerts.")
    p.add_argument("-i", "--interface", help="interface name, e.g. en0 (default: auto-detect)")
    p.add_argument("-t", "--interval", type=float, help="seconds between readings")
    p.add_argument("--warning", type=float, help="WARNING threshold in Mbps (up+down)")
    p.add_argument("--critical", type=float, help="CRITICAL threshold in Mbps (up+down)")
    p.add_argument("-d", "--duration", type=float, help="stop automatically after N seconds")
    p.add_argument("--config", default=os.path.join(ROOT, "config.json"))
    p.add_argument("--list", action="store_true", help="list network interfaces and exit")
    return p.parse_args()


def resolve(path):
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def main() -> int:
    args = parse_args()
    if args.list:
        display.print_interfaces(list_interfaces())
        return 0
    try:
        cfg = load_config(args.config, {
            "interface": args.interface, "interval_seconds": args.interval,
            "warning_mbps": args.warning, "critical_mbps": args.critical})
        iface = select_interface(cfg.interface)
        prev = read_counters(iface.name)
    except (ConfigError, InterfaceError) as exc:
        print(f"Error: {exc}")
        return 1

    logger = MonitorLogger(resolve(cfg.history_file), resolve(cfg.alert_file))
    color = display.supports_color()
    interactive = sys.stdout.isatty()
    events = deque(maxlen=cfg.recent_events_shown)
    capacity = iface.speed_mbps
    capacity_text = f"{capacity} Mbps" if capacity else "Unavailable (not reported by OS)"
    base = prev
    prev_t = time.monotonic()
    start_t = prev_t
    readings = warnings = criticals = 0
    peak_down = peak_up = 0.0

    try:
        while True:
            time.sleep(cfg.interval_seconds)
            try:
                curr = read_counters(iface.name)
            except InterfaceError as exc:
                events.append(f"[{now()}] {exc} Retrying...")
                prev = None
                continue
            t = time.monotonic()
            if prev is None:  # interface came back: restart the baseline
                prev, prev_t = curr, t
                continue
            dt = t - prev_t
            up = calc.compute_rate(prev.bytes_sent, curr.bytes_sent, dt)
            down = calc.compute_rate(prev.bytes_recv, curr.bytes_recv, dt)
            util = calc.utilization_percent(up, down, capacity)
            status = calc.classify(up, down, util, cfg)
            stamp = now()
            msg = calc.message_for(status)
            state = {
                "interface": iface.name, "ip": iface.ipv4, "capacity_text": capacity_text,
                "up_kbps": calc.bytes_to_kbps(up), "down_kbps": calc.bytes_to_kbps(down),
                "up_mbps": calc.bytes_to_mbps(up), "down_mbps": calc.bytes_to_mbps(down),
                "sent_mb": calc.bytes_to_mb(curr.bytes_sent - base.bytes_sent),
                "recv_mb": calc.bytes_to_mb(curr.bytes_recv - base.bytes_recv),
                "pps_out": calc.compute_rate(prev.packets_sent, curr.packets_sent, dt),
                "pps_in": calc.compute_rate(prev.packets_recv, curr.packets_recv, dt),
                "errors": curr.errors - base.errors, "drops": curr.drops - base.drops,
                "utilization": util, "status": status,
            }
            events.append(f"[{stamp}] {msg}")
            logger.log_reading([
                stamp, iface.name, f"{state['up_kbps']:.2f}", f"{state['down_kbps']:.2f}",
                f"{state['up_mbps']:.4f}", f"{state['down_mbps']:.4f}",
                f"{state['sent_mb']:.3f}", f"{state['recv_mb']:.3f}",
                "" if util is None else f"{util:.2f}", status])
            if status != calc.NORMAL:
                logger.log_alert(stamp, iface.name, status, msg)
            readings += 1
            warnings += status == calc.WARNING
            criticals += status == calc.CRITICAL
            peak_down, peak_up = max(peak_down, state["down_kbps"]), max(peak_up, state["up_kbps"])

            screen = display.render(state, list(events), color)
            print(("\033[H\033[J" if interactive else "") + screen, flush=True)
            prev, prev_t = curr, t
            if args.duration and t - start_t >= args.duration:
                break
    except KeyboardInterrupt:
        pass
    finally:
        logger.close()

    print("\n\nMonitoring stopped safely.")
    print(f"Interface: {iface.name} | Readings: {readings} | Warnings: {warnings} | "
          f"Critical: {criticals}")
    print(f"Peak download: {peak_down:.2f} KB/s | Peak upload: {peak_up:.2f} KB/s")
    print(f"History log: {resolve(cfg.history_file)}")
    print(f"Alert log  : {resolve(cfg.alert_file)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
