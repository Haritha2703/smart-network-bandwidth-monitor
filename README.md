# Smart Network Bandwidth Monitoring and Alert System
Computer Networks mini-project - Python 3 + `psutil`, runs in the Terminal (macOS, tested design target: MacBook Air M3).

## What it does
Reads the operating system's real byte counters for one network interface once per second, converts the difference into upload/download speed (KB/s and Mbps), shows total data sent/received, classifies traffic as **NORMAL / WARNING / CRITICAL** with configurable thresholds, and records every reading and alert with a timestamp.

## Important honesty note
This tool measures traffic **of your own computer's interface** (e.g. `en0`). It does **not** see other devices on your Wi-Fi router, and it does **not** inspect packet contents. (Router-wide monitoring would need SNMP or router access - listed as future work.) Link utilisation (%) is shown only when macOS reports a link speed; otherwise it is labelled "Unavailable" - no fake percentage is ever shown. On many Macs Wi-Fi reports no speed, so expect "Unavailable".

## Folder structure
```
Smart-Network-Bandwidth-Monitor/
  main.py                 program entry point (loop, logging, Ctrl+C handling)
  setup_and_run.sh        one-step setup + run
  config.json             thresholds, interval, log paths
  requirements.txt        psutil
  src/interfaces.py       find interfaces, read byte counters
  src/calculator.py       speed maths + alert rules
  src/logger.py           CSV history + alert log
  src/display.py          terminal screen
  src/config.py           config loading/validation
  tests/test_core.py      unit tests
  logs/                   generated: bandwidth_history.csv, alerts.log
  screenshots/            put your own real screenshots here
  presentation/Smart_Network_Bandwidth_Monitoring.pptx
```

## Step-by-step on your MacBook
1. **Download** the ZIP (`Smart-Network-Bandwidth-Monitor.zip`). It usually lands in `Downloads`.
2. **Extract**: double-click the ZIP in Finder. A folder `Smart-Network-Bandwidth-Monitor` appears.
3. **Open in VS Code**: open VS Code -> *File > Open Folder...* -> choose the extracted folder -> *Open*.
4. **Open the terminal**: in VS Code press `` Ctrl + ` `` (or *Terminal > New Terminal*). It opens inside the project folder.
5. **Run** (first time sets everything up automatically):
   ```bash
   chmod +x setup_and_run.sh
   ./setup_and_run.sh
   ```
   If macOS asks to install "Command Line Developer Tools" (Python 3 missing), click *Install*, wait, then run the command again.
6. **Stop** with `Ctrl + C`. A summary and the log locations are printed.

### Manual alternative
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```
Next time just: `source .venv/bin/activate && python main.py`

## Useful options
```bash
python main.py --list                     # show interfaces (name, IP, status)
python main.py -i en0                     # choose an interface
python main.py --warning 2 --critical 8   # easy demo: lower thresholds (Mbps, up+down)
python main.py -t 2                       # refresh every 2 seconds
python main.py -d 30                      # stop automatically after 30 s
python -m unittest discover -s tests -v   # run the tests
```
**Demo tip:** start with `--warning 2 --critical 8`, then play a YouTube video or download a large file to see WARNING/CRITICAL appear.

## Alert logic
- Total throughput = upload + download, in Mbps. `>= warning_mbps` -> WARNING, `>= critical_mbps` -> CRITICAL (defaults 5 and 20; edit `config.json`).
- If the OS reports link capacity: utilisation = busier direction / capacity. `>= 70%` WARNING, `>= 90%` CRITICAL. The more severe result wins.
- Speed = (bytes_now - bytes_before) / seconds_elapsed. Mbps = bytes/s x 8 / 1,000,000. KB/s = bytes/s / 1024.
- "Total Data Sent/Received" counts data since the program started.

## Sample output (illustrative layout - your numbers will differ)
```
====================================================
 SMART NETWORK BANDWIDTH MONITORING AND ALERT SYSTEM
====================================================
Monitoring Status : ACTIVE
Network Interface : en0
IP Address        : 192.168.1.5
Link Capacity     : Unavailable (not reported by OS)

---------------- NETWORK STATISTICS ----------------
Upload Speed      : 35.20 KB/s  (0.288 Mbps)
Download Speed    : 1210.45 KB/s  (9.916 Mbps)
Total Data Sent   : 4.12 MB
Total Data Received: 86.30 MB
Packets/s Out/In  : 120 / 980
Errors / Drops    : 0 / 0 (since start)
Bandwidth Usage   : Unavailable (OS reports no link speed)
Alert Status      : WARNING
----------------------------------------------------

[2026-10-11 13:46:15] Network traffic is normal.
[2026-10-11 13:46:16] WARNING: High bandwidth usage detected!

Monitoring continues... Press CTRL+C to stop.
```

## Troubleshooting
- `command not found: python3` -> install Python 3 (see step 5).
- `Permission denied: ./setup_and_run.sh` -> run `chmod +x setup_and_run.sh`.
- Wrong interface picked -> `python main.py --list`, then `python main.py -i <name>`.
- Speeds always 0 -> you may be monitoring an idle interface; try `-i en0`.

## Testing status
Verified in the author's Linux sandbox (not on macOS): syntax check, 13 unit tests, listing interfaces, missing-interface error, live run on `eth0`, a CRITICAL alert generated from real loopback traffic, CSV/alert logs written, clean exit on Ctrl+C (SIGINT). **Not verified:** macOS/M3 execution, Wi-Fi `en0`, and a live WARNING level (covered by unit tests only). Run it on your Mac and take your own screenshots for the `screenshots/` folder.
