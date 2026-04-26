import time
import os
import json


def tail_log(log_path):
    while not os.path.exists(log_path):
        print(f"Waiting for log file: {log_path}")
        time.sleep(2)
    with open(log_path, "r") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                yield entry
            except json.JSONDecodeError:
                continue
