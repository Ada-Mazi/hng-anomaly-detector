import time
from collections import deque, defaultdict
from threading import Lock


class AnomalyDetector:
    def __init__(self, window_seconds=60, zscore_threshold=3.0, rate_multiplier=5.0, error_multiplier=3.0):
        self.window_seconds = window_seconds
        self.zscore_threshold = zscore_threshold
        self.rate_multiplier = rate_multiplier
        self.error_multiplier = error_multiplier
        self.ip_requests = defaultdict(deque)
        self.ip_errors = defaultdict(deque)
        self.global_requests = deque()
        self.lock = Lock()

    def _evict(self, dq, cutoff):
        while dq and dq[0] < cutoff:
            dq.popleft()

    def record(self, ip, is_error=False):
        now = time.time()
        cutoff = now - self.window_seconds
        with self.lock:
            self.ip_requests[ip].append(now)
            self._evict(self.ip_requests[ip], cutoff)
            if is_error:
                self.ip_errors[ip].append(now)
                self._evict(self.ip_errors[ip], cutoff)
            self.global_requests.append(now)
            self._evict(self.global_requests, cutoff)

    def get_ip_rate(self, ip):
        now = time.time()
        cutoff = now - self.window_seconds
        with self.lock:
            self._evict(self.ip_requests[ip], cutoff)
            return len(self.ip_requests[ip])

    def get_global_rate(self):
        now = time.time()
        cutoff = now - self.window_seconds
        with self.lock:
            self._evict(self.global_requests, cutoff)
            return len(self.global_requests)

    def get_ip_error_rate(self, ip):
        now = time.time()
        cutoff = now - self.window_seconds
        with self.lock:
            self._evict(self.ip_errors[ip], cutoff)
            return len(self.ip_errors[ip])

    def get_top_ips(self, n=10):
        now = time.time()
        cutoff = now - self.window_seconds
        with self.lock:
            counts = {}
            for ip, dq in self.ip_requests.items():
                self._evict(dq, cutoff)
                if dq:
                    counts[ip] = len(dq)
            return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:n]

    def check_ip(self, ip, mean, stddev, error_mean):
        rate = self.get_ip_rate(ip)
        error_rate = self.get_ip_error_rate(ip)
        tightened = error_rate > error_mean * 3
        threshold = self.zscore_threshold * 0.7 if tightened else self.zscore_threshold
        zscore = (rate - mean) / stddev if stddev > 0 else 0
        if zscore > threshold or rate > mean * self.rate_multiplier:
            return True, rate, zscore
        return False, rate, zscore

    def check_global(self, mean, stddev):
        rate = self.get_global_rate()
        zscore = (rate - mean) / stddev if stddev > 0 else 0
        if zscore > self.zscore_threshold or rate > mean * self.rate_multiplier:
            return True, rate, zscore
        return False, rate, zscore
