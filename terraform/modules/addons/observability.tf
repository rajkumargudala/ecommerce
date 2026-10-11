# ===========================================================================
# Full-Stack Observability Addons
# - Prometheus & Grafana (kube-prometheus-stack)
# - Loki & Promtail (Log aggregation)
# - Tempo (Distributed tracing)
# - OpenTelemetry Collector (Unified telemetry ingestion pipeline)
# ===========================================================================

# ---------------------------------------------------------------------------
# 1. Dedicated Namespace for Observability Stack
# ---------------------------------------------------------------------------
resource "kubernetes_namespace_v1" "monitoring" {
  count = var.enable_observability ? 1 : 0

  metadata {
    name = var.observability_namespace
    labels = {
      name                           = var.observability_namespace
      "app.kubernetes.io/part-of"    = "observability"
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }
}

# ---------------------------------------------------------------------------
# 2. Loki (Distributed Log Aggregation)
# ---------------------------------------------------------------------------
resource "helm_release" "loki" {
  count = var.enable_observability && var.enable_loki ? 1 : 0

  name       = "loki"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "loki"
  version    = var.loki_chart_version
  namespace  = kubernetes_namespace_v1.monitoring[0].metadata[0].name

  values = [
    yamlencode({
      deploymentMode = "SingleBinary"
      loki = {
        auth_enabled = false
        commonConfig = {
          replication_factor = 1
        }
        storage = {
          type = "filesystem"
        }
        schemaConfig = {
          configs = [
            {
              from         = "2024-01-01"
              store        = "tsdb"
              object_store = "filesystem"
              schema       = "v13"
              index = {
                prefix = "loki_index_"
                period = "24h"
              }
            }
          ]
        }
      }
      singleBinary = {
        replicas = 1
        persistence = {
          enabled      = true
          storageClass = var.observability_storage_class
          size         = var.loki_storage_size
        }
      }
      backend = {
        replicas = 0
      }
      read = {
        replicas = 0
      }
      write = {
        replicas = 0
      }
      chunksCache = {
        allocatedMemory = 256
      }
      gateway = {
        enabled = false
      }
    })
  ]

  depends_on = [kubernetes_namespace_v1.monitoring]
}

# ---------------------------------------------------------------------------
# 3. Promtail (Node DaemonSet Log Shipper to Loki)
# ---------------------------------------------------------------------------
resource "helm_release" "promtail" {
  count = var.enable_observability && var.enable_loki ? 1 : 0

  name       = "promtail"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "promtail"
  version    = var.promtail_chart_version
  namespace  = kubernetes_namespace_v1.monitoring[0].metadata[0].name

  values = [
    yamlencode({
      config = {
        clients = [
          {
            url = "http://loki.${var.observability_namespace}.svc.cluster.local:3100/loki/api/v1/push"
          }
        ]
      }
    })
  ]

  depends_on = [helm_release.loki]
}

# ---------------------------------------------------------------------------
# 4. Tempo (Distributed Tracing Backend)
# ---------------------------------------------------------------------------
resource "helm_release" "tempo" {
  count = var.enable_observability && var.enable_tempo ? 1 : 0

  name       = "tempo"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "tempo"
  version    = var.tempo_chart_version
  namespace  = kubernetes_namespace_v1.monitoring[0].metadata[0].name

  values = [
    yamlencode({
      tempo = {
        repository = "grafana/tempo"
        retention  = var.tempo_retention
        storage = {
          trace = {
            backend = "local"
            local = {
              path = "/var/tempo/traces"
            }
          }
        }
        receivers = {
          otlp = {
            protocols = {
              grpc = {
                endpoint = "0.0.0.0:4317"
              }
              http = {
                endpoint = "0.0.0.0:4318"
              }
            }
          }
          jaeger = {
            protocols = {
              thrift_http = {
                endpoint = "0.0.0.0:14268"
              }
            }
          }
          zipkin = {
            endpoint = "0.0.0.0:9411"
          }
        }
      }
      persistence = {
        enabled      = true
        storageClass = var.observability_storage_class
        size         = var.tempo_storage_size
      }
    })
  ]

  depends_on = [kubernetes_namespace_v1.monitoring]
}

# ---------------------------------------------------------------------------
# 5. OpenTelemetry Collector (Unified Telemetry Pipeline)
# ---------------------------------------------------------------------------
resource "helm_release" "opentelemetry_collector" {
  count = var.enable_observability && var.enable_opentelemetry ? 1 : 0

  name       = "opentelemetry-collector"
  repository = "https://open-telemetry.github.io/opentelemetry-helm-charts"
  chart      = "opentelemetry-collector"
  version    = var.opentelemetry_collector_chart_version
  namespace  = kubernetes_namespace_v1.monitoring[0].metadata[0].name

  values = [
    yamlencode({
      mode = "deployment"
      config = {
        receivers = {
          otlp = {
            protocols = {
              grpc = {
                endpoint = "0.0.0.0:4317"
              }
              http = {
                endpoint = "0.0.0.0:4318"
              }
            }
          }
        }
        processors = {
          batch = {
            timeout         = "1s"
            send_batch_size = 256
          }
          memory_limiter = {
            check_interval         = "1s"
            limit_percentage       = 75
            spike_limit_percentage = 20
          }
        }
        exporters = {
          # Route traces to Tempo
          otlp = {
            endpoint = "tempo.${var.observability_namespace}.svc.cluster.local:4317"
            tls = {
              insecure = true
            }
          }
          # Expose metrics endpoint for Prometheus scrape
          prometheus = {
            endpoint = "0.0.0.0:8889"
          }
          # Route logs to Loki
          otlphttp = {
            endpoint = "http://loki.${var.observability_namespace}.svc.cluster.local:3100/otlp"
            tls = {
              insecure = true
            }
          }
        }
        service = {
          pipelines = {
            traces = {
              receivers  = ["otlp"]
              processors = ["memory_limiter", "batch"]
              exporters  = ["otlp"]
            }
            metrics = {
              receivers  = ["otlp"]
              processors = ["memory_limiter", "batch"]
              exporters  = ["prometheus"]
            }
            logs = {
              receivers  = ["otlp"]
              processors = ["memory_limiter", "batch"]
              exporters  = ["otlphttp"]
            }
          }
        }
      }
      ports = {
        otlp = {
          enabled       = true
          containerPort = 4317
          servicePort   = 4317
          protocol      = "TCP"
        }
        otlp-http = {
          enabled       = true
          containerPort = 4318
          servicePort   = 4318
          protocol      = "TCP"
        }
        prometheus = {
          enabled       = true
          containerPort = 8889
          servicePort   = 8889
          protocol      = "TCP"
        }
      }
    })
  ]

  depends_on = [
    kubernetes_namespace_v1.monitoring,
    helm_release.tempo,
    helm_release.loki
  ]
}

# ---------------------------------------------------------------------------
# 6. Prometheus & Grafana (kube-prometheus-stack)
# ---------------------------------------------------------------------------
resource "helm_release" "kube_prometheus_stack" {
  count = var.enable_observability && var.enable_prometheus ? 1 : 0

  name       = "kube-prometheus-stack"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  version    = var.kube_prometheus_stack_chart_version
  namespace  = kubernetes_namespace_v1.monitoring[0].metadata[0].name

  values = [
    yamlencode({
      # Prometheus Server Configuration
      prometheus = {
        prometheusSpec = {
          retention = var.prometheus_retention
          storageSpec = {
            volumeClaimTemplate = {
              spec = {
                storageClassName = var.observability_storage_class
                accessModes      = ["ReadWriteOnce"]
                resources = {
                  requests = {
                    storage = var.prometheus_storage_size
                  }
                }
              }
            }
          }
          # Scrape metrics from OpenTelemetry Collector
          additionalScrapeConfigs = [
            {
              job_name        = "opentelemetry-collector"
              scrape_interval = "15s"
              static_configs = [
                {
                  targets = ["opentelemetry-collector.${var.observability_namespace}.svc.cluster.local:8889"]
                }
              ]
            }
          ]
        }
      }

      # Grafana UI & Pre-Configured Correlated DataSources
      grafana = {
        enabled       = var.enable_grafana
        adminPassword = var.grafana_admin_password
        persistence = {
          enabled          = true
          storageClassName = var.observability_storage_class
          size             = var.grafana_storage_size
        }
        additionalDataSources = [
          # 1. Loki DataSource (Logs with Trace-to-Tempo correlation)
          {
            name      = "Loki"
            type      = "loki"
            access    = "proxy"
            url       = "http://loki.${var.observability_namespace}.svc.cluster.local:3100"
            isDefault = false
            jsonData = {
              maxLines = 1000
              derivedFields = [
                {
                  matcherRegex  = "(?:trace_id|traceId|traceID|trace)=(\\w+)"
                  name          = "TraceID"
                  url           = "$${__value.raw}"
                  datasourceUid = "tempo"
                }
              ]
            }
          },
          # 2. Tempo DataSource (Traces with Trace-to-Logs & Trace-to-Metrics)
          {
            name      = "Tempo"
            type      = "tempo"
            access    = "proxy"
            url       = "http://tempo.${var.observability_namespace}.svc.cluster.local:3100"
            uid       = "tempo"
            isDefault = false
            jsonData = {
              httpMethod = "GET"
              tracesToLogs = {
                datasourceUid = "Loki"
                tags          = ["app", "service.name", "k8s.pod.name"]
                filterByTrace = true
                filterBySpan  = true
              }
              tracesToMetrics = {
                datasourceUid = "Prometheus"
                tags          = [{ key = "service.name", value = "service" }]
                queries = [
                  {
                    name  = "Request rate"
                    query = "sum(rate(http_requests_total{$$__tags}[1m]))"
                  }
                ]
              }
            }
          }
        ]
      }

      alertmanager = {
        enabled = true
      }
      nodeExporter = {
        enabled = true
      }
      kubeStateMetrics = {
        enabled = true
      }
    })
  ]

  depends_on = [
    kubernetes_namespace_v1.monitoring,
    helm_release.loki,
    helm_release.tempo,
    helm_release.opentelemetry_collector
  ]
}
