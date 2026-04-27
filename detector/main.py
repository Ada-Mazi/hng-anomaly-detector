import time
import threading
from config import load_config
from monitor import tail_log
from baseline import BaselineTracker
from detector import AnomalyDetector
from blocker import Blocker
from unbanner import Unbanner
from notifier import Notifier
from audit import AuditLog
from dashboard import run_dashboard, update_state

cfg = load_config()

baseline = BaselineTracker(
    window_minutes=cfg['baseline_window_minutes'],
    recalc_interval=cfg['baseline_recalc_interval']
)
detector = AnomalyDetector(
    window_seconds=cfg['sliding_window_seconds'],
    zscore_threshold=cfg['zscore_threshold'],
    rate_multiplier=cfg['rate_multiplier_threshold'],
    error_multiplier=cfg['error_rate_multiplier']
)
blocker = Blocker()
notifier = Notifier(cfg['slack_webhook_url'])
audit = AuditLog(cfg['audit_log_path'])
unbanner = Unbanner(blocker, notifier, audit, cfg['unban_schedule'])

print('HNG Anomaly Detector starting...')

def monitor_loop():
    last_global_alert = 0
    for entry in tail_log(cfg['log_path']):
        ip = entry.get('source_ip', '').split(',')[0].strip()
        status = int(entry.get('status', 200))
        is_error = status >= 400

        if not ip or ip == '-':
            continue

        print('Processing request from IP: ' + ip)

        baseline.record_request(is_error=is_error)
        detector.record(ip, is_error=is_error)

        recalculated = baseline.maybe_recalculate()
        mean, stddev, error_mean = baseline.get_baseline()

        if recalculated:
            audit.log_baseline(mean, stddev)
            print('Baseline recalculated: mean=' + str(round(mean,2)) + ' stddev=' + str(round(stddev,2)))

        update_state(
            blocker.get_banned(),
            detector.get_global_rate(),
            detector.get_top_ips(),
            mean,
            stddev
        )

        banned = blocker.get_banned()

        if ip not in banned:
            anomalous, rate, zscore = detector.check_ip(ip, mean, stddev, error_mean)
            if anomalous:
                success = blocker.ban(ip)
                if success:
                    count = blocker.get_ban_count(ip)
                    schedule = cfg['unban_schedule']
                    duration = schedule[min(count - 1, len(schedule) - 1)]
                    notifier.send_ban(ip, rate, mean, duration)
                    audit.log_ban(ip, 'zscore=' + str(round(zscore, 2)), rate, mean, duration)
                    unbanner.schedule_unban(ip, time.time())
                    print('BANNED: ' + ip)

        now = time.time()
        if now - last_global_alert > 60:
            g_anomalous, g_rate, g_zscore = detector.check_global(mean, stddev)
            if g_anomalous:
                notifier.send_global_alert(g_rate, mean, g_zscore)
                last_global_alert = now
                print('GLOBAL ALERT: rate=' + str(g_rate))

threading.Thread(target=unbanner.run, daemon=True).start()
threading.Thread(target=monitor_loop, daemon=True).start()

run_dashboard(cfg['dashboard_port'])
