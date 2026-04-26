import time
import psutil
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

_state = {
    'banned_ips': {},
    'global_rps': 0,
    'top_ips': [],
    'mean': 1.0,
    'stddev': 0.5,
    'uptime_start': time.time(),
}

HTML = (
    '<!DOCTYPE html><html><head><title>HNG Anomaly Detector</title>'
    '<meta http-equiv="refresh" content="3">'
    '<style>'
    'body{font-family:monospace;background:#0d1117;color:#c9d1d9;padding:20px}'
    'h1{color:#58a6ff}h2{color:#f0883e;margin-top:30px}'
    'table{border-collapse:collapse;width:100%;margin-top:10px}'
    'th,td{border:1px solid #30363d;padding:8px 12px;text-align:left}'
    'th{background:#161b22;color:#58a6ff}'
    'tr:nth-child(even){background:#161b22}'
    '.red{color:#ff7b72;font-weight:bold}'
    '.stat{display:inline-block;margin:10px 20px 10px 0;padding:10px 20px;'
    'background:#161b22;border-radius:8px;border:1px solid #30363d}'
    '.label{font-size:12px;color:#8b949e}'
    '.value{font-size:24px;color:#58a6ff;font-weight:bold}'
    '</style></head><body>'
    '<h1>HNG Anomaly Detector Dashboard</h1>'
    '<div>'
    '<div class="stat"><div class="label">Global Req/s</div><div class="value">{{ rps }}</div></div>'
    '<div class="stat"><div class="label">Banned IPs</div><div class="value red">{{ banned_count }}</div></div>'
    '<div class="stat"><div class="label">Baseline Mean</div><div class="value">{{ mean }}</div></div>'
    '<div class="stat"><div class="label">StdDev</div><div class="value">{{ stddev }}</div></div>'
    '<div class="stat"><div class="label">CPU</div><div class="value">{{ cpu }}%</div></div>'
    '<div class="stat"><div class="label">Memory</div><div class="value">{{ mem }}%</div></div>'
    '<div class="stat"><div class="label">Uptime</div><div class="value">{{ uptime }}</div></div>'
    '</div>'
    '<h2>Banned IPs</h2>'
    '<table><tr><th>IP</th><th>Banned At</th></tr>'
    '{% for ip,ts in banned_ips.items() %}<tr><td class="red">{{ ip }}</td><td>{{ ts }}</td></tr>{% else %}'
    '<tr><td colspan="2">None</td></tr>{% endfor %}'
    '</table>'
    '<h2>Top 10 IPs (last 60s)</h2>'
    '<table><tr><th>IP</th><th>Requests</th></tr>'
    '{% for ip,count in top_ips %}<tr><td>{{ ip }}</td><td>{{ count }}</td></tr>{% else %}'
    '<tr><td colspan="2">No data</td></tr>{% endfor %}'
    '</table>'
    '</body></html>'
)


@app.route('/')
def index():
    uptime_secs = int(time.time() - _state['uptime_start'])
    h = uptime_secs // 3600
    m = (uptime_secs % 3600) // 60
    s = uptime_secs % 60
    banned_fmt = {}
    for ip, ts in _state['banned_ips'].items():
        banned_fmt[ip] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))
    return render_template_string(HTML,
        rps=round(_state['global_rps'] / 60, 2),
        banned_count=len(_state['banned_ips']),
        mean=round(_state['mean'], 2),
        stddev=round(_state['stddev'], 2),
        cpu=psutil.cpu_percent(),
        mem=psutil.virtual_memory().percent,
        uptime=str(h) + 'h ' + str(m) + 'm ' + str(s) + 's',
        banned_ips=banned_fmt,
        top_ips=_state['top_ips'],
    )


@app.route('/api/stats')
def stats():
    return jsonify({
        'global_rps': round(_state['global_rps'] / 60, 2),
        'banned_ips': list(_state['banned_ips'].keys()),
        'top_ips': _state['top_ips'],
        'mean': round(_state['mean'], 2),
        'stddev': round(_state['stddev'], 2),
        'cpu': psutil.cpu_percent(),
        'mem': psutil.virtual_memory().percent,
        'uptime': int(time.time() - _state['uptime_start']),
    })


def update_state(banned, global_rate, top_ips, mean, stddev):
    _state['banned_ips'] = banned
    _state['global_rps'] = global_rate
    _state['top_ips'] = top_ips
    _state['mean'] = mean
    _state['stddev'] = stddev


def run_dashboard(port=5000):
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
