import json
import os
import subprocess

true = True
false = False
null = None

PROM_DS = {"type": "prometheus", "uid": "prometheus"}
LOKI_DS = {"type": "loki", "uid": "P8E80F9AEF21F6940"}
TEMPO_DS = {"type": "tempo", "uid": "tempo"}

def build_overview_dashboard():
    dashboard = {
        "annotations": {
            "list": [
                {
                    "builtIn": 1,
                    "datasource": "-- Grafana --",
                    "enable": True,
                    "hide": true,
                    "name": "Annotations & Alerts",
                    "type": "dashboard"
                }
            ]
        },
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 1,
        "id": None,
        "links": [
            {
                "asDropdown": False,
                "icon": "dashboard",
                "includeVars": True,
                "keepTime": True,
                "tags": ["ecommerce"],
                "targetBlank": False,
                "title": "eCommerce Navigation",
                "type": "dashboards"
            }
        ],
        "liveNow": False,
        "panels": [
            # Row 1: Header / Health Status of Microservices
            {
                "collapsed": False,
                "gridPos": {"h": 1, "w": 24, "x": 0, "y": 0},
                "id": 100,
                "title": "Microservices Health Status",
                "type": "row"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "mappings": [
                            {"options": {"0": {"color": "red", "index": 0, "text": "DOWN"}}, "type": "value"},
                            {"options": {"from": 1, "to": 100, "result": {"color": "green", "index": 1, "text": "HEALTHY"}}, "type": "range"}
                        ],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [{"color": "red", "value": None}, {"color": "green", "value": 1}]
                        }
                    }
                },
                "gridPos": {"h": 3, "w": 3, "x": 0, "y": 1},
                "id": 1,
                "options": {
                    "colorMode": "background",
                    "graphMode": "none",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "textMode": "auto"
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'sum(kube_deployment_status_replicas_available{namespace="default", deployment="frontend"}) or vector(0)',
                        "instant": True,
                        "legendFormat": "Frontend (React)",
                        "refId": "A"
                    }
                ],
                "title": "Frontend (Web UI)",
                "type": "stat"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "mappings": [
                            {"options": {"0": {"color": "red", "index": 0, "text": "DOWN"}}, "type": "value"},
                            {"options": {"from": 1, "to": 100, "result": {"color": "green", "index": 1, "text": "HEALTHY"}}, "type": "range"}
                        ],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [{"color": "red", "value": None}, {"color": "green", "value": 1}]
                        }
                    }
                },
                "gridPos": {"h": 3, "w": 3, "x": 3, "y": 1},
                "id": 2,
                "options": {
                    "colorMode": "background",
                    "graphMode": "none",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "textMode": "auto"
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'sum(kube_deployment_status_replicas_available{namespace="default", deployment="auth-service"}) or vector(0)',
                        "instant": True,
                        "legendFormat": "Auth (Java 21)",
                        "refId": "A"
                    }
                ],
                "title": "Auth Service",
                "type": "stat"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "mappings": [
                            {"options": {"0": {"color": "red", "index": 0, "text": "DOWN"}}, "type": "value"},
                            {"options": {"from": 1, "to": 100, "result": {"color": "green", "index": 1, "text": "HEALTHY"}}, "type": "range"}
                        ],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [{"color": "red", "value": None}, {"color": "green", "value": 1}]
                        }
                    }
                },
                "gridPos": {"h": 3, "w": 3, "x": 6, "y": 1},
                "id": 3,
                "options": {
                    "colorMode": "background",
                    "graphMode": "none",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "textMode": "auto"
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'sum(kube_deployment_status_replicas_available{namespace="default", deployment="catalog-service"}) or vector(0)',
                        "instant": True,
                        "legendFormat": "Catalog (Go)",
                        "refId": "A"
                    }
                ],
                "title": "Catalog Service",
                "type": "stat"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "mappings": [
                            {"options": {"0": {"color": "red", "index": 0, "text": "DOWN"}}, "type": "value"},
                            {"options": {"from": 1, "to": 100, "result": {"color": "green", "index": 1, "text": "HEALTHY"}}, "type": "range"}
                        ],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [{"color": "red", "value": None}, {"color": "green", "value": 1}]
                        }
                    }
                },
                "gridPos": {"h": 3, "w": 3, "x": 9, "y": 1},
                "id": 4,
                "options": {
                    "colorMode": "background",
                    "graphMode": "none",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "textMode": "auto"
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'sum(kube_deployment_status_replicas_available{namespace="default", deployment="inventory-service"}) or vector(0)',
                        "instant": True,
                        "legendFormat": "Inventory (Node.js)",
                        "refId": "A"
                    }
                ],
                "title": "Inventory Service",
                "type": "stat"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "mappings": [
                            {"options": {"0": {"color": "red", "index": 0, "text": "DOWN"}}, "type": "value"},
                            {"options": {"from": 1, "to": 100, "result": {"color": "green", "index": 1, "text": "HEALTHY"}}, "type": "range"}
                        ],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [{"color": "red", "value": None}, {"color": "green", "value": 1}]
                        }
                    }
                },
                "gridPos": {"h": 3, "w": 3, "x": 12, "y": 1},
                "id": 5,
                "options": {
                    "colorMode": "background",
                    "graphMode": "none",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "textMode": "auto"
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'sum(kube_deployment_status_replicas_available{namespace="default", deployment="order-service"}) or vector(0)',
                        "instant": True,
                        "legendFormat": "Order (Python)",
                        "refId": "A"
                    }
                ],
                "title": "Order Service",
                "type": "stat"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "mappings": [
                            {"options": {"0": {"color": "red", "index": 0, "text": "DOWN"}}, "type": "value"},
                            {"options": {"from": 1, "to": 100, "result": {"color": "green", "index": 1, "text": "HEALTHY"}}, "type": "range"}
                        ],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [{"color": "red", "value": None}, {"color": "green", "value": 1}]
                        }
                    }
                },
                "gridPos": {"h": 3, "w": 3, "x": 15, "y": 1},
                "id": 6,
                "options": {
                    "colorMode": "background",
                    "graphMode": "none",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "textMode": "auto"
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'sum(kube_deployment_status_replicas_available{namespace="default", deployment="payment-service"}) or vector(0)',
                        "instant": True,
                        "legendFormat": "Payment (.NET)",
                        "refId": "A"
                    }
                ],
                "title": "Payment Service",
                "type": "stat"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "mappings": [
                            {"options": {"0": {"color": "red", "index": 0, "text": "DOWN"}}, "type": "value"},
                            {"options": {"from": 1, "to": 100, "result": {"color": "green", "index": 1, "text": "HEALTHY"}}, "type": "range"}
                        ],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [{"color": "red", "value": None}, {"color": "green", "value": 1}]
                        }
                    }
                },
                "gridPos": {"h": 3, "w": 3, "x": 18, "y": 1},
                "id": 7,
                "options": {
                    "colorMode": "background",
                    "graphMode": "none",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "textMode": "auto"
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'sum(kube_deployment_status_replicas_available{namespace="default", deployment="notification-service"}) or vector(0)',
                        "instant": True,
                        "legendFormat": "Notification (Ruby)",
                        "refId": "A"
                    }
                ],
                "title": "Notification Service",
                "type": "stat"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "mappings": [
                            {"options": {"0": {"color": "red", "index": 0, "text": "DOWN"}}, "type": "value"},
                            {"options": {"from": 1, "to": 100, "result": {"color": "green", "index": 1, "text": "HEALTHY"}}, "type": "range"}
                        ],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [{"color": "red", "value": None}, {"color": "green", "value": 1}]
                        }
                    }
                },
                "gridPos": {"h": 3, "w": 3, "x": 21, "y": 1},
                "id": 8,
                "options": {
                    "colorMode": "background",
                    "graphMode": "none",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "textMode": "auto"
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'sum(kube_deployment_status_replicas_available{namespace="default", deployment="analytics-service"}) or vector(0)',
                        "instant": True,
                        "legendFormat": "Analytics (PHP)",
                        "refId": "A"
                    }
                ],
                "title": "Analytics Service",
                "type": "stat"
            },

            # Row 2: Aggregate Metrics & KPIs
            {
                "collapsed": False,
                "gridPos": {"h": 1, "w": 24, "x": 0, "y": 4},
                "id": 101,
                "title": "Platform Health & Resource KPIs",
                "type": "row"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]}
                    }
                },
                "gridPos": {"h": 4, "w": 4, "x": 0, "y": 5},
                "id": 9,
                "options": {
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "textMode": "auto"
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'sum(kube_deployment_status_replicas_available{namespace="default"})',
                        "instant": True,
                        "legendFormat": "Available Pods",
                        "refId": "A"
                    }
                ],
                "title": "Running App Replicas",
                "type": "stat"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]}
                    }
                },
                "gridPos": {"h": 4, "w": 4, "x": 4, "y": 5},
                "id": 10,
                "options": {
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "textMode": "auto"
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'sum(kube_statefulset_status_replicas_ready{namespace="default"})',
                        "instant": True,
                        "legendFormat": "Dedicated Databases",
                        "refId": "A"
                    }
                ],
                "title": "Active Dedicated Databases",
                "type": "stat"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [{"color": "green", "value": None}, {"color": "yellow", "value": 1}, {"color": "red", "value": 5}]
                        }
                    }
                },
                "gridPos": {"h": 4, "w": 4, "x": 8, "y": 5},
                "id": 11,
                "options": {
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "textMode": "auto"
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'sum(increase(kube_pod_container_status_restarts_total{namespace="default"}[1h])) or vector(0)',
                        "instant": True,
                        "legendFormat": "Restarts",
                        "refId": "A"
                    }
                ],
                "title": "Pod Restarts (Past 1h)",
                "type": "stat"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "unit": "cores"
                    }
                },
                "gridPos": {"h": 4, "w": 4, "x": 12, "y": 5},
                "id": 12,
                "options": {
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "textMode": "auto"
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'sum(rate(container_cpu_usage_seconds_total{namespace="default", container!=""}[5m]))',
                        "instant": True,
                        "legendFormat": "Total CPU",
                        "refId": "A"
                    }
                ],
                "title": "Total App CPU Usage",
                "type": "stat"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "unit": "bytes"
                    }
                },
                "gridPos": {"h": 4, "w": 4, "x": 16, "y": 5},
                "id": 13,
                "options": {
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "textMode": "auto"
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'sum(container_memory_working_set_bytes{namespace="default", container!=""})',
                        "instant": True,
                        "legendFormat": "Total Memory",
                        "refId": "A"
                    }
                ],
                "title": "Total App Memory (Working Set)",
                "type": "stat"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "unit": "binBps"
                    }
                },
                "gridPos": {"h": 4, "w": 4, "x": 20, "y": 5},
                "id": 14,
                "options": {
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "textMode": "auto"
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'sum(rate(container_network_receive_bytes_total{namespace="default"}[5m])) + sum(rate(container_network_transmit_bytes_total{namespace="default"}[5m]))',
                        "instant": True,
                        "legendFormat": "Network I/O",
                        "refId": "A"
                    }
                ],
                "title": "Total Network Throughput",
                "type": "stat"
            },

            # Row 3: CPU & Memory Breakdown
            {
                "collapsed": False,
                "gridPos": {"h": 1, "w": 24, "x": 0, "y": 9},
                "id": 102,
                "title": "Resource Consumption by Microservice",
                "type": "row"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "custom": {
                            "drawStyle": "line",
                            "lineInterpolation": "smooth",
                            "lineWidth": 2,
                            "fillOpacity": 15
                        },
                        "unit": "cores"
                    }
                },
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 10},
                "id": 15,
                "options": {
                    "legend": {"calcs": ["mean", "max", "lastNotNull"], "displayMode": "table", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "multi", "sort": "desc"}
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'sum by (container) (rate(container_cpu_usage_seconds_total{namespace="default", container!=""}[5m]))',
                        "legendFormat": "{{container}}",
                        "refId": "A"
                    }
                ],
                "title": "CPU Usage by Service",
                "type": "timeseries"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "custom": {
                            "drawStyle": "line",
                            "lineInterpolation": "smooth",
                            "lineWidth": 2,
                            "fillOpacity": 15
                        },
                        "unit": "bytes"
                    }
                },
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 10},
                "id": 16,
                "options": {
                    "legend": {"calcs": ["mean", "max", "lastNotNull"], "displayMode": "table", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "multi", "sort": "desc"}
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'sum by (container) (container_memory_working_set_bytes{namespace="default", container!=""})',
                        "legendFormat": "{{container}}",
                        "refId": "A"
                    }
                ],
                "title": "Memory Usage (Working Set) by Service",
                "type": "timeseries"
            },

            # Row 4: Dedicated Databases Storage & Persistence
            {
                "collapsed": False,
                "gridPos": {"h": 1, "w": 24, "x": 0, "y": 18},
                "id": 103,
                "title": "Dedicated Databases Storage & Health (gp3 Volumes)",
                "type": "row"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "max": 100,
                        "min": 0,
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [{"color": "green", "value": None}, {"color": "#EAB839", "value": 75}, {"color": "red", "value": 90}]
                        },
                        "unit": "percent"
                    }
                },
                "gridPos": {"h": 7, "w": 12, "x": 0, "y": 19},
                "id": 17,
                "options": {
                    "displayMode": "gradient",
                    "orientation": "horizontal",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "showUnfilled": True
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'kubelet_volume_stats_used_bytes{namespace="default"} / kubelet_volume_stats_capacity_bytes{namespace="default"} * 100',
                        "instant": True,
                        "legendFormat": "{{persistentvolumeclaim}}",
                        "refId": "A"
                    }
                ],
                "title": "Database PVC Capacity Used (%)",
                "type": "bargauge"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "custom": {
                            "drawStyle": "line",
                            "lineInterpolation": "linear",
                            "lineWidth": 2,
                            "fillOpacity": 10
                        },
                        "unit": "bytes"
                    }
                },
                "gridPos": {"h": 7, "w": 12, "x": 12, "y": 19},
                "id": 18,
                "options": {
                    "legend": {"calcs": ["lastNotNull"], "displayMode": "table", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "single"}
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'kubelet_volume_stats_used_bytes{namespace="default"}',
                        "legendFormat": "{{persistentvolumeclaim}} Used",
                        "refId": "A"
                    }
                ],
                "title": "Database PVC Disk Space Consumed (Bytes)",
                "type": "timeseries"
            },

            # Row 5: Centralized Log Activity
            {
                "collapsed": False,
                "gridPos": {"h": 1, "w": 24, "x": 0, "y": 26},
                "id": 104,
                "title": "Centralized Application Log Activity (Loki)",
                "type": "row"
            },
            {
                "datasource": LOKI_DS,
                "fieldConfig": {
                    "defaults": {
                        "custom": {
                            "drawStyle": "bars",
                            "lineWidth": 1,
                            "fillOpacity": 60,
                            "stacking": {"group": "A", "mode": "normal"}
                        },
                        "unit": "short"
                    }
                },
                "gridPos": {"h": 7, "w": 24, "x": 0, "y": 27},
                "id": 19,
                "options": {
                    "legend": {"calcs": ["sum", "lastNotNull"], "displayMode": "table", "placement": "right", "showLegend": True},
                    "tooltip": {"mode": "multi", "sort": "desc"}
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": LOKI_DS,
                        "expr": 'sum by (app) (rate({namespace="default"}[1m]))',
                        "legendFormat": "{{app}}",
                        "refId": "A"
                    }
                ],
                "title": "Application Log Streams Ingestion Rate",
                "type": "timeseries"
            }
        ],
        "refresh": "10s",
        "schemaVersion": 39,
        "tags": ["ecommerce", "platform", "microservices", "overview"],
        "templating": {"list": []},
        "time": {"from": "now-1h", "to": "now"},
        "timepicker": {"refresh_intervals": ["5s", "10s", "30s", "1m", "5m"]},
        "timezone": "browser",
        "title": "eCommerce Platform - Application Overview",
        "uid": "ecommerce-overview",
        "version": 1
    }
    return dashboard

def build_services_dashboard():
    dashboard = {
        "annotations": {"list": []},
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 1,
        "id": None,
        "links": [
            {
                "asDropdown": False,
                "icon": "dashboard",
                "includeVars": True,
                "keepTime": True,
                "tags": ["ecommerce"],
                "targetBlank": False,
                "title": "eCommerce Navigation",
                "type": "dashboards"
            }
        ],
        "liveNow": False,
        "panels": [
            # Row 1: Key Service KPIs
            {
                "collapsed": False,
                "gridPos": {"h": 1, "w": 24, "x": 0, "y": 0},
                "id": 200,
                "title": "Service Details & Health Metrics",
                "type": "row"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]}
                    }
                },
                "gridPos": {"h": 4, "w": 6, "x": 0, "y": 1},
                "id": 21,
                "options": {
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "textMode": "auto"
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'count(kube_pod_info{namespace="default", pod=~"$pod"})',
                        "instant": True,
                        "legendFormat": "Active Pods",
                        "refId": "A"
                    }
                ],
                "title": "Selected Service Pod Count",
                "type": "stat"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [{"color": "green", "value": None}, {"color": "#EAB839", "value": 1}, {"color": "red", "value": 5}]
                        }
                    }
                },
                "gridPos": {"h": 4, "w": 6, "x": 6, "y": 1},
                "id": 22,
                "options": {
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "textMode": "auto"
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'sum(increase(kube_pod_container_status_restarts_total{namespace="default", container=~"$service", pod=~"$pod"}[24h])) or vector(0)',
                        "instant": True,
                        "legendFormat": "Restarts",
                        "refId": "A"
                    }
                ],
                "title": "Pod Restarts (Past 24h)",
                "type": "stat"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "unit": "cores"
                    }
                },
                "gridPos": {"h": 4, "w": 6, "x": 12, "y": 1},
                "id": 23,
                "options": {
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "textMode": "auto"
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'sum(rate(container_cpu_usage_seconds_total{namespace="default", container=~"$service", pod=~"$pod"}[5m]))',
                        "instant": True,
                        "legendFormat": "CPU",
                        "refId": "A"
                    }
                ],
                "title": "Current CPU Usage",
                "type": "stat"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "unit": "bytes"
                    }
                },
                "gridPos": {"h": 4, "w": 6, "x": 18, "y": 1},
                "id": 24,
                "options": {
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "textMode": "auto"
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'sum(container_memory_working_set_bytes{namespace="default", container=~"$service", pod=~"$pod"})',
                        "instant": True,
                        "legendFormat": "Memory",
                        "refId": "A"
                    }
                ],
                "title": "Current Memory (Working Set)",
                "type": "stat"
            },

            # Row 2: Performance Graphs
            {
                "collapsed": False,
                "gridPos": {"h": 1, "w": 24, "x": 0, "y": 5},
                "id": 201,
                "title": "CPU & Memory Performance Analysis",
                "type": "row"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "custom": {
                            "drawStyle": "line",
                            "lineInterpolation": "smooth",
                            "lineWidth": 2,
                            "fillOpacity": 15
                        },
                        "unit": "cores"
                    }
                },
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 6},
                "id": 25,
                "options": {
                    "legend": {"calcs": ["mean", "max", "lastNotNull"], "displayMode": "table", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "multi", "sort": "desc"}
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'rate(container_cpu_usage_seconds_total{namespace="default", container=~"$service", pod=~"$pod"}[5m])',
                        "legendFormat": "{{pod}} (Used)",
                        "refId": "A"
                    },
                    {
                        "datasource": PROM_DS,
                        "expr": 'kube_pod_container_resource_requests{namespace="default", container=~"$service", pod=~"$pod", resource="cpu"}',
                        "legendFormat": "{{pod}} (Request)",
                        "refId": "B"
                    },
                    {
                        "datasource": PROM_DS,
                        "expr": 'kube_pod_container_resource_limits{namespace="default", container=~"$service", pod=~"$pod", resource="cpu"}',
                        "legendFormat": "{{pod}} (Limit)",
                        "refId": "C"
                    }
                ],
                "title": "CPU Usage vs Request & Limit",
                "type": "timeseries"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "custom": {
                            "drawStyle": "line",
                            "lineInterpolation": "smooth",
                            "lineWidth": 2,
                            "fillOpacity": 15
                        },
                        "unit": "bytes"
                    }
                },
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 6},
                "id": 26,
                "options": {
                    "legend": {"calcs": ["mean", "max", "lastNotNull"], "displayMode": "table", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "multi", "sort": "desc"}
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'container_memory_working_set_bytes{namespace="default", container=~"$service", pod=~"$pod"}',
                        "legendFormat": "{{pod}} (Used)",
                        "refId": "A"
                    },
                    {
                        "datasource": PROM_DS,
                        "expr": 'kube_pod_container_resource_requests{namespace="default", container=~"$service", pod=~"$pod", resource="memory"}',
                        "legendFormat": "{{pod}} (Request)",
                        "refId": "B"
                    },
                    {
                        "datasource": PROM_DS,
                        "expr": 'kube_pod_container_resource_limits{namespace="default", container=~"$service", pod=~"$pod", resource="memory"}',
                        "legendFormat": "{{pod}} (Limit)",
                        "refId": "C"
                    }
                ],
                "title": "Memory Usage (Working Set) vs Request & Limit",
                "type": "timeseries"
            },

            # Row 3: Throttling & Network
            {
                "collapsed": False,
                "gridPos": {"h": 1, "w": 24, "x": 0, "y": 14},
                "id": 202,
                "title": "Throttling & Network I/O",
                "type": "row"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "custom": {
                            "drawStyle": "line",
                            "lineInterpolation": "linear",
                            "lineWidth": 2,
                            "fillOpacity": 15
                        },
                        "unit": "s"
                    }
                },
                "gridPos": {"h": 7, "w": 12, "x": 0, "y": 15},
                "id": 27,
                "options": {
                    "legend": {"calcs": ["mean", "max"], "displayMode": "table", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "multi"}
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'rate(container_cpu_cfs_throttled_seconds_total{namespace="default", container=~"$service", pod=~"$pod"}[5m])',
                        "legendFormat": "{{pod}} throttled",
                        "refId": "A"
                    }
                ],
                "title": "CPU Throttling Rate (CGroup Throttled Seconds)",
                "type": "timeseries"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "custom": {
                            "drawStyle": "line",
                            "lineInterpolation": "linear",
                            "lineWidth": 2,
                            "fillOpacity": 10
                        },
                        "unit": "binBps"
                    }
                },
                "gridPos": {"h": 7, "w": 12, "x": 12, "y": 15},
                "id": 28,
                "options": {
                    "legend": {"calcs": ["mean", "max", "lastNotNull"], "displayMode": "table", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "multi"}
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'rate(container_network_receive_bytes_total{namespace="default", pod=~"$pod"}[5m])',
                        "legendFormat": "{{pod}} (Rx - Inbound)",
                        "refId": "A"
                    },
                    {
                        "datasource": PROM_DS,
                        "expr": 'rate(container_network_transmit_bytes_total{namespace="default", pod=~"$pod"}[5m])',
                        "legendFormat": "{{pod}} (Tx - Outbound)",
                        "refId": "B"
                    }
                ],
                "title": "Network Bandwidth (Rx/Tx)",
                "type": "timeseries"
            },

            # Row 4: Pod Inventory Table
            {
                "collapsed": False,
                "gridPos": {"h": 1, "w": 24, "x": 0, "y": 22},
                "id": 203,
                "title": "Pod Status & Node Placement Inventory",
                "type": "row"
            },
            {
                "datasource": PROM_DS,
                "fieldConfig": {
                    "defaults": {
                        "custom": {"align": "auto", "displayMode": "auto"}
                    }
                },
                "gridPos": {"h": 7, "w": 24, "x": 0, "y": 23},
                "id": 29,
                "options": {"showHeader": True},
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": PROM_DS,
                        "expr": 'kube_pod_info{namespace="default", pod=~"$pod"}',
                        "format": "table",
                        "instant": True,
                        "refId": "A"
                    }
                ],
                "title": "Active Pod Inventory & Placement",
                "transformations": [
                    {
                        "id": "organize",
                        "options": {
                            "excludeByName": {
                                "Time": True,
                                "Value": True,
                                "__name__": True,
                                "created_by_kind": False,
                                "created_by_name": False,
                                "endpoint": True,
                                "instance": True,
                                "job": True,
                                "namespace": True,
                                "service": True,
                                "uid": True
                            },
                            "indexByName": {
                                "pod": 0,
                                "pod_ip": 1,
                                "node": 2,
                                "host_ip": 3,
                                "created_by_kind": 4,
                                "created_by_name": 5
                            },
                            "renameByName": {
                                "created_by_kind": "Controller Kind",
                                "created_by_name": "Controller Name",
                                "host_ip": "Node IP",
                                "node": "EKS Node",
                                "pod": "Pod Name",
                                "pod_ip": "Pod IP"
                            }
                        }
                    }
                ],
                "type": "table"
            }
        ],
        "refresh": "10s",
        "schemaVersion": 39,
        "tags": ["ecommerce", "services", "deep-dive"],
        "templating": {
            "list": [
                {
                    "current": {"selected": True, "text": "auth-service", "value": "auth-service"},
                    "datasource": PROM_DS,
                    "definition": 'label_values(kube_pod_container_info{namespace="default"}, container)',
                    "hide": 0,
                    "includeAll": False,
                    "label": "Microservice",
                    "multi": False,
                    "name": "service",
                    "options": [],
                    "query": {"query": 'label_values(kube_pod_container_info{namespace="default"}, container)', "refId": "StandardVariableQuery"},
                    "refresh": 1,
                    "regex": "",
                    "skipUrlSync": False,
                    "sort": 1,
                    "type": "query"
                },
                {
                    "allValue": ".*",
                    "current": {"selected": True, "text": "All", "value": "$__all"},
                    "datasource": PROM_DS,
                    "definition": 'label_values(kube_pod_info{namespace="default", pod=~"$service.*"}, pod)',
                    "hide": 0,
                    "includeAll": True,
                    "label": "Pod Instance",
                    "multi": True,
                    "name": "pod",
                    "options": [],
                    "query": {"query": 'label_values(kube_pod_info{namespace="default", pod=~"$service.*"}, pod)', "refId": "StandardVariableQuery"},
                    "refresh": 1,
                    "regex": "",
                    "skipUrlSync": False,
                    "sort": 1,
                    "type": "query"
                }
            ]
        },
        "time": {"from": "now-1h", "to": "now"},
        "timepicker": {"refresh_intervals": ["5s", "10s", "30s", "1m", "5m"]},
        "timezone": "browser",
        "title": "eCommerce Microservices - Deep Dive & Performance",
        "uid": "ecommerce-services",
        "version": 1
    }
    return dashboard

def build_logs_dashboard():
    dashboard = {
        "annotations": {"list": []},
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 1,
        "id": None,
        "links": [
            {
                "asDropdown": False,
                "icon": "dashboard",
                "includeVars": True,
                "keepTime": True,
                "tags": ["ecommerce"],
                "targetBlank": False,
                "title": "eCommerce Navigation",
                "type": "dashboards"
            }
        ],
        "liveNow": False,
        "panels": [
            # Row 1: Log Stats
            {
                "collapsed": False,
                "gridPos": {"h": 1, "w": 24, "x": 0, "y": 0},
                "id": 300,
                "title": "Log Metrics & Incident Signals",
                "type": "row"
            },
            {
                "datasource": LOKI_DS,
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [{"color": "green", "value": None}, {"color": "#EAB839", "value": 1}, {"color": "red", "value": 10}]
                        }
                    }
                },
                "gridPos": {"h": 4, "w": 8, "x": 0, "y": 1},
                "id": 31,
                "options": {
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "textMode": "auto"
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": LOKI_DS,
                        "expr": 'sum(count_over_time({namespace="default", app=~"$service"} |~ "(?i)(error|exception|fatal|failed)" [1h])) or vector(0)',
                        "instant": True,
                        "legendFormat": "Errors",
                        "refId": "A"
                    }
                ],
                "title": "Error Logs (Past 1h)",
                "type": "stat"
            },
            {
                "datasource": LOKI_DS,
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [{"color": "green", "value": None}, {"color": "#EAB839", "value": 10}, {"color": "orange", "value": 50}]
                        }
                    }
                },
                "gridPos": {"h": 4, "w": 8, "x": 8, "y": 1},
                "id": 32,
                "options": {
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "textMode": "auto"
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": LOKI_DS,
                        "expr": 'sum(count_over_time({namespace="default", app=~"$service"} |~ "(?i)(warn|warning)" [1h])) or vector(0)',
                        "instant": True,
                        "legendFormat": "Warnings",
                        "refId": "A"
                    }
                ],
                "title": "Warning Logs (Past 1h)",
                "type": "stat"
            },
            {
                "datasource": LOKI_DS,
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"}
                    }
                },
                "gridPos": {"h": 4, "w": 8, "x": 16, "y": 1},
                "id": 33,
                "options": {
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "textMode": "auto"
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": LOKI_DS,
                        "expr": 'sum(count_over_time({namespace="default", app=~"$service"} [1h])) or vector(0)',
                        "instant": True,
                        "legendFormat": "Total Lines",
                        "refId": "A"
                    }
                ],
                "title": "Total Log Lines (Past 1h)",
                "type": "stat"
            },

            # Row 2: Ingestion & Error Rates
            {
                "collapsed": False,
                "gridPos": {"h": 1, "w": 24, "x": 0, "y": 5},
                "id": 301,
                "title": "Log Volumes & Error Frequency",
                "type": "row"
            },
            {
                "datasource": LOKI_DS,
                "fieldConfig": {
                    "defaults": {
                        "custom": {
                            "drawStyle": "bars",
                            "lineWidth": 1,
                            "fillOpacity": 50,
                            "stacking": {"group": "A", "mode": "normal"}
                        },
                        "unit": "short"
                    }
                },
                "gridPos": {"h": 7, "w": 12, "x": 0, "y": 6},
                "id": 34,
                "options": {
                    "legend": {"calcs": ["sum", "lastNotNull"], "displayMode": "table", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "multi"}
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": LOKI_DS,
                        "expr": 'sum by (app) (rate({namespace="default", app=~"$service"}[1m]))',
                        "legendFormat": "{{app}}",
                        "refId": "A"
                    }
                ],
                "title": "Log Rate by Service (Lines / sec)",
                "type": "timeseries"
            },
            {
                "datasource": LOKI_DS,
                "fieldConfig": {
                    "defaults": {
                        "custom": {
                            "drawStyle": "line",
                            "lineInterpolation": "smooth",
                            "lineWidth": 2,
                            "fillOpacity": 20
                        },
                        "unit": "short"
                    }
                },
                "gridPos": {"h": 7, "w": 12, "x": 12, "y": 6},
                "id": 35,
                "options": {
                    "legend": {"calcs": ["sum", "max"], "displayMode": "table", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "multi"}
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": LOKI_DS,
                        "expr": 'sum by (app) (rate({namespace="default", app=~"$service"} |~ "(?i)(error|exception|fatal|failed)" [1m]))',
                        "legendFormat": "{{app}} (Errors)",
                        "refId": "A"
                    }
                ],
                "title": "Error Rate over Time",
                "type": "timeseries"
            },

            # Row 3: Live Application Log Stream
            {
                "collapsed": False,
                "gridPos": {"h": 1, "w": 24, "x": 0, "y": 13},
                "id": 302,
                "title": "Live Application Log Stream",
                "type": "row"
            },
            {
                "datasource": LOKI_DS,
                "gridPos": {"h": 12, "w": 24, "x": 0, "y": 14},
                "id": 36,
                "options": {
                    "dedupStrategy": "none",
                    "enableLogDetails": True,
                    "prettifyLogMessage": True,
                    "showCommonLabels": False,
                    "showLabels": True,
                    "showTime": True,
                    "sortOrder": "Descending",
                    "wrapLogMessage": True
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": LOKI_DS,
                        "expr": '{namespace="default", app=~"$service"} |= "$search"',
                        "refId": "A"
                    }
                ],
                "title": "Live Logs Explorer (Click line to view TraceID link to Tempo)",
                "type": "logs"
            },

            # Row 4: Errors Stream
            {
                "collapsed": False,
                "gridPos": {"h": 1, "w": 24, "x": 0, "y": 26},
                "id": 303,
                "title": "Filtered Errors & Exceptions Stream",
                "type": "row"
            },
            {
                "datasource": LOKI_DS,
                "gridPos": {"h": 10, "w": 24, "x": 0, "y": 27},
                "id": 37,
                "options": {
                    "dedupStrategy": "none",
                    "enableLogDetails": True,
                    "prettifyLogMessage": True,
                    "showCommonLabels": False,
                    "showLabels": True,
                    "showTime": True,
                    "sortOrder": "Descending",
                    "wrapLogMessage": True
                },
                "pluginVersion": "11.1.0",
                "targets": [
                    {
                        "datasource": LOKI_DS,
                        "expr": '{namespace="default", app=~"$service"} |~ "(?i)(error|exception|fatal|failed)" |= "$search"',
                        "refId": "A"
                    }
                ],
                "title": "Errors & Exceptions Stream",
                "type": "logs"
            }
        ],
        "refresh": "10s",
        "schemaVersion": 39,
        "tags": ["ecommerce", "logs", "loki", "tempo"],
        "templating": {
            "list": [
                {
                    "allValue": ".*",
                    "current": {"selected": True, "text": "All", "value": "$__all"},
                    "datasource": PROM_DS,
                    "definition": 'label_values(kube_pod_container_info{namespace="default"}, container)',
                    "hide": 0,
                    "includeAll": True,
                    "label": "Application / Service",
                    "multi": True,
                    "name": "service",
                    "options": [],
                    "query": {"query": 'label_values(kube_pod_container_info{namespace="default"}, container)', "refId": "StandardVariableQuery"},
                    "refresh": 1,
                    "regex": "",
                    "skipUrlSync": False,
                    "sort": 1,
                    "type": "query"
                },
                {
                    "current": {"selected": False, "text": "", "value": ""},
                    "hide": 0,
                    "label": "Search Keyword",
                    "name": "search",
                    "options": [{"selected": True, "text": "", "value": ""}],
                    "query": "",
                    "skipUrlSync": False,
                    "type": "textbox"
                }
            ]
        },
        "time": {"from": "now-1h", "to": "now"},
        "timepicker": {"refresh_intervals": ["5s", "10s", "30s", "1m", "5m"]},
        "timezone": "browser",
        "title": "eCommerce Centralized Logs & Traces Explorer",
        "uid": "ecommerce-logs",
        "version": 1
    }
    return dashboard

if __name__ == "__main__":
    out_dir = "/home/ubuntu/ecommerce/monitoring/dashboards"
    os.makedirs(out_dir, exist_ok=True)
    
    d1 = build_overview_dashboard()
    d2 = build_services_dashboard()
    d3 = build_logs_dashboard()
    
    with open(os.path.join(out_dir, "ecommerce-overview.json"), "w") as f:
        json.dump(d1, f, indent=2)
        
    with open(os.path.join(out_dir, "ecommerce-services.json"), "w") as f:
        json.dump(d2, f, indent=2)
        
    with open(os.path.join(out_dir, "ecommerce-logs.json"), "w") as f:
        json.dump(d3, f, indent=2)
        
    print("Dashboards written successfully.")
