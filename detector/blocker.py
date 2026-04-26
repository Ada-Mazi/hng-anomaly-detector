import subprocess
import time
from threading import Lock


class Blocker:
    def __init__(self):
        self.banned = {}
        self.ban_counts = {}
        self.lock = Lock()

    def ban(self, ip):
        with self.lock:
            if ip in self.banned:
                return False
            try:
                subprocess.run(
                    ["iptables", "-I", "INPUT", "-s", ip, "-j", "DROP"],
                    check=True, capture_output=True
                )
                self.banned[ip] = time.time()
                self.ban_counts[ip] = self.ban_counts.get(ip, 0) + 1
                return True
            except subprocess.CalledProcessError as e:
                print(f"Failed to ban {ip}: {e}")
                return False

    def unban(self, ip):
        with self.lock:
            if ip not in self.banned:
                return False
            try:
                subprocess.run(
                    ["iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"],
                    check=True, capture_output=True
                )
                del self.banned[ip]
                return True
            except subprocess.CalledProcessError as e:
                print(f"Failed to unban {ip}: {e}")
                return False

    def get_banned(self):
        with self.lock:
            return dict(self.banned)

    def get_ban_count(self, ip):
        return self.ban_counts.get(ip, 0)
