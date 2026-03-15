#!/usr/bin/env python3
"""
Autoresearch Dashboard — Live visualization of prompt optimization.

Reads results.jsonl and serves a live-updating dashboard. Automatically
detects criteria from the data — works with any config.

Usage:
    python3 dashboard.py
    python3 dashboard.py --config my_skill.yaml --port 8501
"""

import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

import yaml

# ─── Defaults (overridden by --config) ───────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent / "data"
RESULTS_FILE = BASE_DIR / "results.jsonl"
STATE_FILE = BASE_DIR / "state.json"
PROMPT_FILE = BASE_DIR / "prompt.txt"
BEST_PROMPT_FILE = BASE_DIR / "best_prompt.txt"

SKILL_NAME = "Autoresearch"
CRITERIA_LABELS = {}  # name -> label, populated from config or data
BATCH_SIZE = 10


def load_config_labels(config_path: str | None):
    """Load criteria labels and name from config if available."""
    global SKILL_NAME, CRITERIA_LABELS, BATCH_SIZE, BASE_DIR, RESULTS_FILE, STATE_FILE, PROMPT_FILE, BEST_PROMPT_FILE

    if config_path and Path(config_path).exists():
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        SKILL_NAME = cfg.get("name", "Autoresearch")
        BATCH_SIZE = cfg.get("batch_size", 10)
        for c in cfg.get("evaluation", {}).get("criteria", []):
            CRITERIA_LABELS[c["name"]] = c.get("label", c["name"])

        # Derive paths from config location
        base = Path(config_path).resolve().parent / "data"
        BASE_DIR = base
        RESULTS_FILE = base / "results.jsonl"
        STATE_FILE = base / "state.json"
        PROMPT_FILE = base / "prompt.txt"
        BEST_PROMPT_FILE = base / "best_prompt.txt"


def get_criteria_label(name: str) -> str:
    """Get display label for a criterion, falling back to titlecase."""
    if name in CRITERIA_LABELS:
        return CRITERIA_LABELS[name]
    return name.replace("_", " ").title()


# ─── HTML Template ───────────────────────────────────────────────────────────

def build_html(criteria_names: list[str]) -> str:
    """Build the dashboard HTML dynamically based on discovered criteria."""
    criteria_charts_html = ""
    criteria_headers = ""
    criteria_cells = ""
    chart_inits = ""
    chart_updates = ""
    chart_vars = ""

    colors = [
        ("#8e44ad", "rgba(142,68,173,0.12)"),
        ("#2980b9", "rgba(41,128,185,0.12)"),
        ("#27ae60", "rgba(39,174,96,0.12)"),
        ("#d35400", "rgba(211,84,0,0.12)"),
        ("#c0392b", "rgba(192,57,43,0.12)"),
        ("#16a085", "rgba(22,160,133,0.12)"),
        ("#f39c12", "rgba(243,156,18,0.12)"),
        ("#2c3e50", "rgba(44,62,80,0.12)"),
    ]

    for i, name in enumerate(criteria_names):
        label = get_criteria_label(name)
        color, color_light = colors[i % len(colors)]
        canvas_id = f"chart_{name}"
        var_name = f"chart_{name}"

        criteria_charts_html += f"""
  <div class="criteria-chart">
    <h3>{label}</h3>
    <canvas id="{canvas_id}"></canvas>
  </div>"""

        criteria_headers += f"<th>{label}</th>"
        criteria_cells += f"<td>${{r.criteria?.{name} ?? '?'}}/{SKILL_NAME != 'Autoresearch' and BATCH_SIZE or 10}</td>"

        chart_vars += f"let {var_name};\n"
        chart_inits += f"  {var_name} = createChart('{canvas_id}', '{label}', batchSize, '{color}', '{color_light}');\n"
        chart_updates += f"  updateCriterionChart({var_name}, labels, runs.map(r => r.criteria?.{name} ?? 0));\n"

    return r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>""" + SKILL_NAME + r""" — Autoresearch</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #faf9f7; color: #2d2a26; padding: 32px; max-width: 1200px; margin: 0 auto; }

  .header { display: flex; align-items: center; gap: 16px; margin-bottom: 32px; }
  .header h1 { font-size: 28px; font-weight: 700; color: #2d2a26; }
  .badge { background: #c0392b; color: white; font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 4px; letter-spacing: 1px; }
  .subtitle { color: #8a8580; font-size: 14px; margin-top: 4px; }

  .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 32px; }
  .stat-card { background: white; border-radius: 12px; padding: 20px 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
  .stat-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: #8a8580; margin-bottom: 8px; }
  .stat-value { font-size: 36px; font-weight: 700; }
  .stat-value.green { color: #27ae60; }
  .stat-value.orange { color: #c0784a; }
  .stat-value.neutral { color: #2d2a26; }

  .chart-container { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); margin-bottom: 32px; }
  .chart-container canvas { width: 100% !important; height: 300px !important; }

  .criteria-charts { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 32px; }
  .criteria-chart { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
  .criteria-chart h3 { font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: #8a8580; margin-bottom: 12px; }
  .criteria-chart canvas { width: 100% !important; height: 160px !important; }

  .table-container { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); margin-bottom: 32px; }
  .table-container h3 { font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: #8a8580; margin-bottom: 16px; }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: #8a8580; padding: 8px 12px; border-bottom: 1px solid #eee; }
  td { padding: 10px 12px; border-bottom: 1px solid #f5f4f2; font-size: 14px; }
  .status-keep { color: #27ae60; font-weight: 600; }
  .status-discard { color: #8a8580; }

  .prompt-container { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
  .prompt-container h3 { font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: #8a8580; margin-bottom: 12px; }
  .prompt-text { font-family: 'SF Mono', 'Fira Code', monospace; font-size: 13px; line-height: 1.6; color: #4a4540; white-space: pre-wrap; word-break: break-word; background: #faf9f7; padding: 16px; border-radius: 8px; max-height: 300px; overflow-y: auto; }

  @media (max-width: 768px) {
    .stats { grid-template-columns: repeat(2, 1fr); }
    .criteria-charts { grid-template-columns: 1fr; }
    body { padding: 16px; }
  }
</style>
</head>
<body>

<div class="header">
  <div>
    <div style="display:flex;align-items:center;gap:12px;">
      <h1>""" + SKILL_NAME + r"""</h1>
      <span class="badge" id="live-badge">LIVE</span>
    </div>
    <div class="subtitle" id="subtitle">Prompt optimization — refreshes every 15s</div>
  </div>
</div>

<div class="stats">
  <div class="stat-card">
    <div class="stat-label">Current Best</div>
    <div class="stat-value orange" id="stat-best">—</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Baseline</div>
    <div class="stat-value neutral" id="stat-baseline">—</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Improvement</div>
    <div class="stat-value green" id="stat-improvement">—</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Runs / Kept</div>
    <div class="stat-value neutral" id="stat-runs">—</div>
  </div>
</div>

<div class="chart-container">
  <canvas id="mainChart"></canvas>
</div>

<div class="criteria-charts">""" + criteria_charts_html + r"""
</div>

<div class="table-container">
  <h3>Run History</h3>
  <table>
    <thead>
      <tr><th>Run</th><th>Status</th><th>Score</th>""" + criteria_headers + r"""<th>Time</th></tr>
    </thead>
    <tbody id="run-table"></tbody>
  </table>
</div>

<div class="prompt-container">
  <h3>Current Best Prompt</h3>
  <div class="prompt-text" id="best-prompt">Loading...</div>
</div>

<script>
const ORANGE = '#c0784a';
const ORANGE_LIGHT = 'rgba(192, 120, 74, 0.15)';
const GREEN = '#27ae60';

const chartDefaults = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { grid: { display: false }, ticks: { font: { size: 11 }, color: '#8a8580' } },
    y: { grid: { color: '#f0efed' }, ticks: { font: { size: 11 }, color: '#8a8580' } }
  }
};

let mainChart;
""" + chart_vars + r"""

function createChart(canvasId, label, maxY, color, colorLight) {
  const ctx = document.getElementById(canvasId).getContext('2d');
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label,
        data: [],
        borderColor: color,
        backgroundColor: colorLight,
        fill: true,
        tension: 0.3,
        pointRadius: 5,
        pointBackgroundColor: [],
        pointBorderColor: color,
        pointBorderWidth: 2,
      }]
    },
    options: {
      ...chartDefaults,
      scales: {
        ...chartDefaults.scales,
        y: { ...chartDefaults.scales.y, min: 0, max: maxY, ticks: { ...chartDefaults.scales.y.ticks, stepSize: maxY <= 10 ? 1 : 5 } }
      }
    }
  });
}

function updateChart(chart, labels, data) {
  chart.data.labels = labels;
  chart.data.datasets[0].data = data;
  let runningBest = -1;
  const colors = data.map(v => {
    if (v > runningBest) { runningBest = v; return ORANGE; }
    return '#c4c0bb';
  });
  chart.data.datasets[0].pointBackgroundColor = colors;
  chart.update('none');
}

function updateCriterionChart(chart, labels, data) {
  chart.data.labels = labels;
  chart.data.datasets[0].data = data;
  let runningBest = -1;
  const colors = data.map(v => {
    if (v > runningBest) { runningBest = v; return chart.data.datasets[0].borderColor; }
    return '#c4c0bb';
  });
  chart.data.datasets[0].pointBackgroundColor = colors;
  chart.update('none');
}

const batchSize = """ + str(BATCH_SIZE) + r""";

function initCharts() {
  const maxScore = batchSize * """ + str(len(criteria_names)) + r""";
  mainChart = createChart('mainChart', 'Score', maxScore, ORANGE, 'rgba(192, 120, 74, 0.15)');
""" + chart_inits + r"""}

function formatTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

const criteriaNames = """ + json.dumps(criteria_names) + r""";
const criteriaLabels = """ + json.dumps({n: get_criteria_label(n) for n in criteria_names}) + r""";

async function refresh() {
  try {
    const res = await fetch('/api/data');
    const data = await res.json();
    if (!data || !data.runs || data.runs.length === 0) return;

    const runs = data.runs;
    const labels = runs.map(r => r.run);
    const scores = runs.map(r => r.score);
    const maxScore = runs[0]?.max || (batchSize * criteriaNames.length);
    const baseline = scores[0];
    const best = Math.max(...scores);

    document.getElementById('stat-best').textContent = best + '/' + maxScore;
    document.getElementById('stat-baseline').textContent = baseline + '/' + maxScore;
    const improvement = baseline > 0 ? ((best - baseline) / baseline * 100).toFixed(1) : '—';
    const improvEl = document.getElementById('stat-improvement');
    improvEl.textContent = improvement === '—' ? '—' : (improvement > 0 ? '+' : '') + improvement + '%';
    improvEl.className = 'stat-value ' + (improvement > 0 ? 'green' : improvement < 0 ? 'orange' : 'neutral');

    let kept = 0, runningBest = -1;
    scores.forEach(s => { if (s > runningBest) { kept++; runningBest = s; } });
    document.getElementById('stat-runs').textContent = runs.length + ' / ' + kept;

    updateChart(mainChart, labels, scores);

""" + chart_updates + r"""
    // Table
    const tbody = document.getElementById('run-table');
    let runningBest2 = -1;
    const statuses = scores.map(s => { if (s > runningBest2) { runningBest2 = s; return 'keep'; } return 'discard'; });
    const rows = runs.map((r, idx) => {
      const st = statuses[idx];
      let critCells = '';
      criteriaNames.forEach(n => {
        critCells += '<td>' + (r.criteria?.[n] ?? '?') + '/' + batchSize + '</td>';
      });
      return '<tr>' +
        '<td>' + r.run + '</td>' +
        '<td class="status-' + st + '">' + st + '</td>' +
        '<td><strong>' + r.score + '/' + maxScore + '</strong></td>' +
        critCells +
        '<td>' + formatTime(r.timestamp) + '</td>' +
        '</tr>';
    }).reverse();
    tbody.innerHTML = rows.join('');

    if (data.best_prompt) {
      document.getElementById('best-prompt').textContent = data.best_prompt;
    }

    const lastRun = runs[runs.length - 1];
    document.getElementById('subtitle').textContent =
      'Prompt optimization — ' + runs.length + ' runs — last: ' + formatTime(lastRun?.timestamp);
  } catch (e) {
    console.error('Fetch error:', e);
  }
}

initCharts();
refresh();
setInterval(refresh, 15000);
</script>
</body>
</html>"""


# ─── Discover criteria from existing data ────────────────────────────────────

def discover_criteria() -> list[str]:
    """Read results.jsonl and extract criteria names from the first entry."""
    if not RESULTS_FILE.exists():
        return []
    for line in RESULTS_FILE.read_text().strip().split("\n"):
        if line.strip():
            try:
                entry = json.loads(line)
                return list(entry.get("criteria", {}).keys())
            except json.JSONDecodeError:
                continue
    return []


# ─── HTTP Handler ────────────────────────────────────────────────────────────

_cached_html = None


class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        global _cached_html
        parsed = urlparse(self.path)

        if parsed.path == "/" or parsed.path == "/index.html":
            if _cached_html is None:
                criteria = discover_criteria()
                if not criteria:
                    criteria = list(CRITERIA_LABELS.keys()) if CRITERIA_LABELS else ["score"]
                _cached_html = build_html(criteria)

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(_cached_html.encode())

        elif parsed.path == "/api/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            runs = []
            if RESULTS_FILE.exists():
                for line in RESULTS_FILE.read_text().strip().split("\n"):
                    if line.strip():
                        try:
                            runs.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass

            best_prompt = ""
            if BEST_PROMPT_FILE.exists():
                best_prompt = BEST_PROMPT_FILE.read_text().strip()

            data = {"runs": runs, "best_prompt": best_prompt}
            self.wfile.write(json.dumps(data).encode())

        elif parsed.path == "/api/refresh-html":
            # Force rebuild HTML (useful when new criteria appear)
            _cached_html = None
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Autoresearch Dashboard")
    parser.add_argument("--port", type=int, default=8501)
    parser.add_argument("--config", default=None, help="Path to YAML config (for labels/name)")
    args = parser.parse_args()

    if args.config:
        load_config_labels(args.config)
    else:
        # Try to find config.yaml in same directory
        default_config = Path(__file__).resolve().parent / "config.yaml"
        if default_config.exists():
            load_config_labels(str(default_config))

    server = HTTPServer(("0.0.0.0", args.port), DashboardHandler)
    print(f"Dashboard: {SKILL_NAME}")
    print(f"  URL: http://localhost:{args.port}")
    print(f"  Data: {RESULTS_FILE}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutdown.")


if __name__ == "__main__":
    main()
