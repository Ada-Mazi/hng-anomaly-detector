import yaml
import os

def load_config():
    with open("/app/config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    cfg["slack_webhook_url"] = os.environ.get("SLACK_WEBHOOK_URL", cfg.get("slack_webhook_url", ""))
    cfg["audit_log_path"] = "/var/log/nginx/audit.log"
    return cfg
