import time
import math
from collections import deque
from threading import Lock


class BaselineTracker:
    def __init__(self, window_minutes=30, recalc_interval=60):
        self.window_seconds = window_minutes * 60
        self.recalc_interval = recalc_interval
        self.per_second_counts = deque()
        self.error_counts = deque()
        self.lock = Lock()
        self.effective_mean = 1.0
        self.effective_stddev = 0.5
        self.error_mean = 0.1
        self.last_recalc = time.time()
        self.hourly_slots = {}
        self.current_second = int(time.time())
        self.current_count = 0
        self.current_errors = 0

    def record_request(self, is_error=False):
        now = int(time.time())
        with self.lock:
            if now != self.current_second:
                self._flush_second(self.current_second, self.current_count, self.current_errors)
                self.current_second = now
                self.current_count = 0
                self.current_errors = 0
            self.current_count += 1
            if is_error:
                self.current_errors += 1

    def _flush_second(self, ts, count, errors):
        cutoff = ts - self.window_seconds
        self.per_second_counts.append((ts, count))
        self.error_counts.append((ts, errors))
        while self.per_second_counts and self.per_second_counts[0][0] < cutoff:
            self.per_second_counts.popleft()
        while self.error_counts and self.error_counts[0][0] < cutoff:
            self.error_counts.popleft()
        hour_slot = ts // 3600
        if hour_slot not in self.hourly_slots:
            self.hourly_slots[hour_slot] = []
        self.hourly_slots[hour_slot].append(count)
        if len(self.hourly_slots) > 25:
            oldest = min(self.hourly_slots.keys())
            del self.hourly_slots[oldest]

    def maybe_recalculate(self):
        now = time.time()
        with self.lock:
            if now - self.last_recalc < self.recalc_interval:
                return False
            self.last_recalc = now
            current_hour = int(now) // 3600
            if current_hour in self.hourly_slots and len(self.hourly_slots[current_hour]) >= 60:
                counts = self.hourly_slots[current_hour]
            else:
                counts = [c for _, c in self.per_second_counts]
            if len(counts) < 10:
                return False
            mean = sum(counts) / len(counts)
            variance = sum((x - mean) ** 2 for x in counts) / len(counts)
            stddev = math.sqrt(variance)
            self.effective_mean = max(mean, 1.0)
            self.effective_stddev = max(stddev, 0.5)
            error_vals = [c for _, c in self.error_counts]
            if error_vals:
                self.error_mean = max(sum(error_vals) / len(error_vals), 0.1)
            return True

    def get_baseline(self):
        with self.lock:
            return self.effective_mean, self.effective_stddev, self.error_mean
