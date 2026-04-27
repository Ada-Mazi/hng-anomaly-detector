import time


class AuditLog:
    def __init__(self, path):
        self.path = path
        self.fallback = '/tmp/audit.log'
        self._ensure_file()

    def _ensure_file(self):
        for p in [self.path, self.fallback]:
            try:
                with open(p, 'a') as f:
                    f.write('')
                self.path = p
                print('Audit log path: ' + p)
                return
            except Exception:
                continue

    def _write(self, line):
        try:
            with open(self.path, 'a') as f:
                f.write(line + chr(10))
            print(line)
        except Exception as e:
            print('Audit log error: ' + str(e))
            try:
                with open(self.fallback, 'a') as f:
                    f.write(line + chr(10))
            except Exception:
                pass

    def log_ban(self, ip, condition, rate, mean, duration):
        ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        line = '[' + ts + '] BAN ip=' + ip + ' | condition=' + str(condition) + ' | rate=' + str(rate) + ' | baseline=' + str(round(mean,2)) + ' | duration=' + str(duration)
        self._write(line)

    def log_unban(self, ip, condition, duration):
        ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        line = '[' + ts + '] UNBAN ip=' + ip + ' | condition=' + str(condition) + ' | duration=' + str(duration)
        self._write(line)

    def log_baseline(self, mean, stddev):
        ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        line = '[' + ts + '] BASELINE_RECALC | effective_mean=' + str(round(mean,2)) + ' | effective_stddev=' + str(round(stddev,2))
        self._write(line)
