# HNG Anomaly Detector — Stage 3

A real-time DDoS/anomaly detection engine built alongside Nextcloud.

## Server Details
- Server IP: 34.31.206.191
- Nextcloud: http://34.31.206.191
- Dashboard: http://hngdevops.mooo.com:8080

## Language
Python — chosen for rapid development, rich stdlib, and ease of statistical computation.

## How the Sliding Window Works
Two deque-based windows track requests over the last 60 seconds — one per IP, one global.
Each request timestamp is appended to the deque. On every check, timestamps older than
60 seconds are evicted from the left side of the deque. The window size is always the
current length of the deque — no counters, no approximations.

## How the Baseline Works
A 30-minute rolling window of per-second request counts is maintained. Every 60 seconds,
mean and stddev are recalculated from this window. Per-hour slots are maintained and the
current hour's data is preferred when it has enough samples (>=60). Floor values prevent
division by zero: mean floor = 1.0, stddev floor = 0.5.

## Detection Logic
An IP or global rate is flagged anomalous if:
- Z-score = (rate - mean) / stddev > 3.0, OR
- Rate > 5x the baseline mean
Whichever fires first triggers a response.

## How iptables Blocks an IP
When an IP is flagged, the detector runs:
  iptables -I INPUT -s <ip> -j DROP
This inserts a DROP rule at the top of the INPUT chain, silently dropping all packets
from that IP. The rule is removed on unban using iptables -D INPUT -s <ip> -j DROP.

## Setup Instructions
1. Clone this repo
2. Install Docker and Docker Compose
3. Set SLACK_WEBHOOK_URL in .env
4. Run: docker compose up -d --build

## GitHub Repo
https://github.com/Ada-Mazi/hng-anomaly-detector
