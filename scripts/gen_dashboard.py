"""Generates helm/stockpilot/dashboards/stockpilot.json (dashboard as code).

    python3 scripts/gen_dashboard.py > helm/stockpilot/dashboards/stockpilot.json
"""
import json, sys

DS = {"type": "prometheus", "uid": "${datasource}"}
J = 'job="$job"'
panels, pid = [], 0

def nxt():
    global pid; pid += 1; return pid

def target(expr, legend="", ref="A"):
    return {"datasource": DS, "expr": expr, "legendFormat": legend, "refId": ref, "range": True}

def stat(title, expr, x, unit="short", decimals=None, thresholds=None, desc=""):
    p = {"id": nxt(), "type": "stat", "title": title, "description": desc, "datasource": DS,
         "gridPos": {"h": 4, "w": 4, "x": x, "y": 0},
         "targets": [target(expr)],
         "options": {"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                     "colorMode": "value", "graphMode": "area", "textMode": "auto", "justifyMode": "auto"},
         "fieldConfig": {"defaults": {"unit": unit, "color": {"mode": "thresholds"},
                         "thresholds": {"mode": "absolute", "steps": thresholds or [{"color": "green", "value": None}]}},
                         "overrides": []}}
    if decimals is not None:
        p["fieldConfig"]["defaults"]["decimals"] = decimals
    panels.append(p)

def series(title, targets, x, y, unit="short", desc="", w=12, stack=False):
    panels.append({"id": nxt(), "type": "timeseries", "title": title, "description": desc, "datasource": DS,
        "gridPos": {"h": 8, "w": w, "x": x, "y": y},
        "targets": [target(e, l, chr(65 + i)) for i, (e, l) in enumerate(targets)],
        "options": {"legend": {"displayMode": "list", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "multi", "sort": "desc"}},
        "fieldConfig": {"defaults": {"unit": unit, "custom": {"lineWidth": 2, "fillOpacity": 12,
                        "showPoints": "never", "stacking": {"mode": "normal" if stack else "none", "group": "A"}}},
                        "overrides": []}})

stat("Request rate", f'sum(rate(http_requests_total{{{J}}}[1m]))', 0, "reqps", 2, desc="All API requests per second")
stat("p95 latency", f'histogram_quantile(0.95, sum by (le) (rate(http_request_duration_highr_seconds_bucket{{{J}}}[5m])))', 4, "s", 3,
     [{"color": "green", "value": None}, {"color": "orange", "value": 0.25}, {"color": "red", "value": 0.5}])
stat("5xx error rate", f'(sum(rate(http_requests_total{{{J},status="5xx"}}[5m])) or vector(0)) / clamp_min(sum(rate(http_requests_total{{{J}}}[5m])), 1e-9)', 8,
     "percentunit", 2, [{"color": "green", "value": None}, {"color": "orange", "value": 0.01}, {"color": "red", "value": 0.05}])
stat("Backend targets UP", f'sum(up{{{J}}})', 12, "short", 0, [{"color": "red", "value": None}, {"color": "green", "value": 1}],
     desc="Pods Prometheus is successfully scraping")
stat("HPA replicas", 'max(kube_horizontalpodautoscaler_status_current_replicas{namespace="$namespace", horizontalpodautoscaler="$job"})', 16, "short", 0)
stat("Stock movements (1h)", f'sum(increase(stockpilot_stock_movements_total{{{J}}}[1h]))', 20, "short", 0, desc="Receipts + shipments + adjustments")

series("Requests per second by endpoint",
       [(f'sum by (method, handler) (rate(http_requests_total{{{J}}}[1m]))', "{{method}} {{handler}}")], 0, 4, "reqps")
series("API latency percentiles",
       [(f'histogram_quantile({q}, sum by (le) (rate(http_request_duration_highr_seconds_bucket{{{J}}}[1m])))', f"p{int(q*100)}")
        for q in (0.5, 0.95, 0.99)], 12, 4, "s")
series("Responses by status class",
       [(f'sum by (status) (rate(http_requests_total{{{J}}}[1m]))', "{{status}}")], 0, 12, "reqps", stack=True)
series("Backend CPU per pod (HPA input)",
       [('sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="$namespace", container="backend"}[1m]))', "{{pod}}"),
        ('max(kube_pod_container_resource_requests{namespace="$namespace", container="backend", resource="cpu"})', "CPU request")],
       12, 12, "cores", desc="HPA scales when average usage exceeds 60% of the request")
series("HPA replicas",
       [('max(kube_horizontalpodautoscaler_status_current_replicas{namespace="$namespace", horizontalpodautoscaler="$job"})', "current"),
        ('max(kube_horizontalpodautoscaler_status_desired_replicas{namespace="$namespace", horizontalpodautoscaler="$job"})', "desired"),
        ('max(kube_horizontalpodautoscaler_spec_max_replicas{namespace="$namespace", horizontalpodautoscaler="$job"})', "max")],
       0, 20, "short")
series("Stock movements per minute",
       [(f'sum by (movement_type) (rate(stockpilot_stock_movements_total{{{J}}}[5m])) * 60', "{{movement_type}}"),
        (f'sum(rate(stockpilot_rejected_shipments_total{{{J}}}[5m])) * 60', "rejected shipments")],
       12, 20, "short")

dashboard = {
    "uid": "stockpilot-overview", "title": "StockPilot / Overview", "tags": ["stockpilot", "fastapi"],
    "timezone": "browser", "schemaVersion": 39, "version": 1, "editable": True, "graphTooltip": 1,
    "refresh": "10s", "time": {"from": "now-30m", "to": "now"},
    "templating": {"list": [
        {"name": "datasource", "label": "Data source", "type": "datasource", "query": "prometheus",
         "current": {"text": "Prometheus", "value": "prometheus"}, "hide": 0},
        {"name": "job", "label": "Backend job", "type": "query", "datasource": DS,
         "query": {"query": "label_values(http_requests_total, job)", "refId": "job"},
         "definition": "label_values(http_requests_total, job)", "refresh": 2, "includeAll": False, "hide": 0,
         "current": {"text": "stockpilot-backend", "value": "stockpilot-backend"}},
        {"name": "namespace", "label": "Namespace", "type": "query", "datasource": DS,
         "query": {"query": 'label_values(up{job="$job"}, namespace)', "refId": "ns"},
         "definition": 'label_values(up{job="$job"}, namespace)', "refresh": 2, "includeAll": False, "hide": 0,
         "current": {"text": "stockpilot", "value": "stockpilot"}},
    ]},
    "panels": panels,
}
json.dump(dashboard, sys.stdout, indent=2)
