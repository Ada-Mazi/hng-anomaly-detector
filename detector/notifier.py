import requests
import time


def send_slack(webhook_url, message):
    if not webhook_url:
        print('[SLACK] ' + message)
        return
    try:
        requests.post(webhook_url, json={'text': message}, timeout=5)
    except Exception as e:
        print('Slack error: ' + str(e))


class Notifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_ban(self, ip, rate, mean, duration):
        msg = 'IP BANNED\n'
        msg += 'IP: ' + ip + '\n'
        msg += 'Condition: Rate anomaly detected\n'
        msg += 'Current rate: ' + str(rate) + ' req/60s\n'
        msg += 'Baseline mean: ' + str(round(mean, 2)) + '\n'
        msg += 'Ban duration: ' + str(duration) + 's\n'
        msg += 'Timestamp: ' + time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        send_slack(self.webhook_url, msg)

    def send_unban(self, ip, next_duration):
        msg = 'IP UNBANNED\n'
        msg += 'IP: ' + ip + '\n'
        msg += 'Next ban duration: ' + str(next_duration) + '\n'
        msg += 'Timestamp: ' + time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        send_slack(self.webhook_url, msg)

    def send_global_alert(self, rate, mean, zscore):
        msg = 'GLOBAL TRAFFIC ANOMALY\n'
        msg += 'Condition: Global request rate spike\n'
        msg += 'Current rate: ' + str(rate) + ' req/60s\n'
        msg += 'Baseline mean: ' + str(round(mean, 2)) + '\n'
        msg += 'Z-score: ' + str(round(zscore, 2)) + '\n'
        msg += 'Timestamp: ' + time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
        send_slack(self.webhook_url, msg)
