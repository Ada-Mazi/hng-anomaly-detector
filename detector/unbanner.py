import time
import threading


class Unbanner:
    def __init__(self, blocker, notifier, audit, unban_schedule):
        self.blocker = blocker
        self.notifier = notifier
        self.audit = audit
        self.unban_schedule = unban_schedule
        self.pending = {}
        self.lock = threading.Lock()

    def schedule_unban(self, ip, ban_time):
        count = self.blocker.get_ban_count(ip)
        if count <= len(self.unban_schedule):
            duration = self.unban_schedule[count - 1]
        else:
            duration = self.unban_schedule[-1]
        if duration == 'permanent':
            return
        with self.lock:
            self.pending[ip] = ban_time + duration

    def run(self):
        while True:
            now = time.time()
            to_unban = []
            with self.lock:
                for ip, unban_time in list(self.pending.items()):
                    if now >= unban_time:
                        to_unban.append(ip)
            for ip in to_unban:
                success = self.blocker.unban(ip)
                if success:
                    with self.lock:
                        del self.pending[ip]
                    count = self.blocker.get_ban_count(ip)
                    if count < len(self.unban_schedule):
                        next_dur = self.unban_schedule[count]
                    else:
                        next_dur = 'permanent'
                    self.notifier.send_unban(ip, next_dur)
                    self.audit.log_unban(ip, 'auto-unban', next_dur)
            time.sleep(5)
