# TraceFace Monitoring & Observability Guide

Complete guide to monitoring, alerting, and observability for TraceFace production deployment.

---

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        TraceFace API                         │
│                          Port 8000                           │
│                        /metrics                              │
└────────────────────┬────────────────────────────────────────┘
                     │ Scrape (10s)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                       Prometheus                              │
│                          Port 9090                           │
│                   Time-series database                       │
│                    Alert evaluation                          │
└────────────┬───────────────────────┬─────────────────────────┘
             │                       │
             │ Push alerts           │ Query
             ▼                       ▼
┌───────────────────────┐  ┌─────────────────────────────────┐
│   Alertmanager         │  │         Grafana                 │
│      Port 9093         │  │          Port 3000              │
│  Notification routing  │  │   Dashboards & visualization    │
│  (PagerDuty, Slack,   │  │   (Real-time monitoring)        │
│   Email, etc.)         │  └─────────────────────────────────┘
└───────────────────────┘
```

---

## 🚀 Quick Start

### 1. Start Monitoring Stack

```bash
cd monitoring
docker-compose up -d
```

### 2. Access Dashboards

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **TraceFace API**: http://localhost:8000/metrics

### 3. Import Grafana Dashboard

1. Open Grafana → Dashboards → Import
2. Upload `monitoring/grafana/dashboards/traceface-main.json`
3. Select Prometheus datasource
4. Click "Import"

---

## 📈 Metrics Collected

### HTTP Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests by method, endpoint, status |
| `http_request_duration_seconds` | Histogram | Request latency distribution |
| `http_requests_in_progress` | Gauge | Currently processing requests |

### OSINT Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `osint_requests_total` | Counter | Total OSINT queries by engine |
| `osint_success_total` | Counter | Successful OSINT searches |
| `osint_failure_total` | Counter | Failed searches by error type |
| `osint_candidates_total` | Counter | Discovered candidates by platform |
| `osint_duration_seconds` | Histogram | Search latency by engine |
| `osint_api_quota_remaining` | Gauge | API quota remaining |

### Vision Pipeline Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `vision_face_detections_total` | Counter | Face detections by status |
| `vision_embedding_extractions_total` | Counter | Embedding vectors extracted |
| `vision_liveness_checks_total` | Counter | Liveness checks by result |
| `vision_duration_seconds` | Histogram | Pipeline stage latency |

### Biometric Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `biometric_verifications_total` | Counter | Total verification attempts |
| `biometric_matches_total` | Counter | Successful matches |
| `biometric_rejections_total` | Counter | Rejections below threshold |
| `biometric_similarity_scores` | Histogram | Similarity score distribution |

### Blockchain Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `blockchain_transactions_total` | Counter | Transactions by status |
| `blockchain_gas_used_total` | Counter | Total gas consumed |
| `blockchain_gas_price_gwei` | Gauge | Current gas price |
| `blockchain_eth_balance` | Gauge | Deployer account balance |
| `blockchain_client_connected` | Gauge | Connection status |

### IPFS Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `ipfs_pins_total` | Counter | Pin operations by status |
| `ipfs_pin_duration_seconds` | Histogram | Pin operation latency |
| `ipfs_pinata_quota_remaining` | Gauge | Pinata quota remaining |

### System Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `graph_db_size_bytes` | Gauge | Database file size |
| `queued_scans_total` | Gauge | Scans queued |
| `active_scans_total` | Gauge | Scans in progress |
| `scans_total` | Counter | Total scans by status |

---

## 🚨 Alerting

### Alert Severity Levels

| Level | Response Time | Notification |
|-------|--------------|--------------|
| **Critical** | < 5 minutes | PagerDuty + Slack + Email |
| **Warning** | < 30 minutes | Slack + Email |
| **Info** | Review daily | Email summary |

### Critical Alerts

| Alert | Condition | Impact |
|-------|-----------|--------|
| `APIDown` | API unreachable | Service down |
| `APIDeploymentError` | > 5% 5xx errors | Service degraded |
| `BlockchainDisconnected` | RPC unreachable | Cannot register provenance |
| `AllOSINTEnginesFailed` | No successful searches | No new candidates |
| `LowETHBalance` | < 0.1 ETH remaining | Cannot pay for gas |
| `DiskSpaceLow` | < 10% disk space | Risk of data loss |

### Warning Alerts

| Alert | Condition | Impact |
|-------|-----------|--------|
| `APISlowResponseTime` | p95 > 2s | Performance issue |
| `OSINTSuccessRateLow` | < 50% success | API issues |
| `HighGasPrice` | > 100 Gwei | Expensive transactions |
| `HighMemoryUsage` | > 90% | Needs scaling |
| `IPFSPinningFailures` | > 5% failure | Storage issue |

### Alert Routing

```yaml
# alertmanager.yml
route:
  receiver: 'default'
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 1h

  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true

    - match:
        severity: warning
      receiver: 'slack'
      continue: true

receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: <PAGERDUTY_KEY>

  - name: 'slack'
    slack_configs:
      - api_url: <SLACK_WEBHOOK>
        channel: '#traceface-alerts'

  - name: 'email'
    email_configs:
      - to: 'team@example.com'
        from: 'alerts@traceface.com'
        smarthost: 'smtp.example.com:587'
```

---

## 📊 Grafana Dashboards

### Main Dashboard Panels

1. **API Request Rate** (Graph)
   - Tracks requests per second
   - Filter by method, endpoint

2. **API Response Time** (Histogram)
   - p50/p95/p99 latencies
   - Enables SLO tracking

3. **OSINT Engine Success Rate** (Gauge)
   - Per-engine success percentages
   - Alert threshold: 80%

4. **Biometric Match Rate** (Pie Chart)
   - Matches vs rejections
   - Shows effectiveness

5. **Blockchain Transactions** (Time Series)
   - Success/failure trends
   - Gas usage over time

6. **Platform Distribution** (Pie Chart)
   - Candidates by platform
   - Shows source diversity

7. **Error Rate** (Graph)
   - Errors by type
   - Enables debugging

8. **System Resources** (Graph)
   - CPU, memory, disk
   - Capacity planning

### Dashboard Variables

| Variable | Values | Purpose |
|----------|--------|---------|
| `$datasource` | Prometheus | Switch between environments |
| `$platform` | All, Twitter, Reddit, etc. | Filter by platform |
| `$engine` | All, Google Lens, Bing, etc. | Filter by OSINT engine |
| `$interval` | 5m, 1h, 1d | Time range selection |

---

## 🔧 Configuration

### Prometheus

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'traceface-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

### Grafana

```yaml
# monitoring/grafana/provisioning/datasources/datasources.yml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

### Alertmanager

```yaml
# monitoring/alertmanager.yml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 1h
  receiver: 'default'
```

---

## 🚀 Deployment

### Docker Compose

```yaml
# monitoring/docker-compose.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alert_rules.yml:/etc/prometheus/alert_rules.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml

volumes:
  prometheus-data:
  grafana-data:
```

### Start Stack

```bash
cd monitoring
docker-compose up -d

# Verify
docker-compose ps

# View logs
docker-compose logs -f prometheus
docker-compose logs -f grafana

# Stop
docker-compose down
```

---

## 📝 SLOs & SLIs

### Service Level Objectives

| SLO | Target | Measurement |
|-----|--------|-------------|
| **Availability** | 99.5% | `/up` metric |
| **Latency (p95)** | < 500ms | HTTP duration |
| **Error Rate** | < 1% | HTTP 5xx rate |
| **OSINT Success** | > 80% | Success/requests |
| **Match Rate** | > 20% | Matches/verifications |

### SLI Dashboards

Track these indicators weekly:
- API availability percentage
- p95/p99 latency trends
- Error budget remaining
- Gas cost per transaction
- OSINT coverage per platform

---

## 🛠️ Troubleshooting

### Metrics Not Appearing

1. Check `/metrics` endpoint is accessible
   ```bash
   curl http://localhost:8000/metrics
   ```

2. Verify Prometheus is scraping
   ```bash
   curl http://localhost:9090/api/v1/targets
   ```

3. Check Prometheus logs
   ```bash
   docker-compose logs prometheus
   ```

### High Cardinality Issues

If metrics explode in size:
1. Reduce label cardinality
2. Use recording rules for aggregation
3. Increase scrape interval

### Alert Fatigue

If too many alerts:
1. Adjust alert thresholds
2. Increase `for` duration
3. Use alert silencing

---

## 📚 Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Alertmanager Configuration](https://prometheus.io/docs/alerting/alertmanager/)
- [Instrumenting Python Apps](https://prometheus.io/docs/guides/python-application/)

---

## ✅ Checklist

Before production:

- [ ] Prometheus scraping `/metrics`
- [ ] Grafana dashboards imported
- [ ] Alert rules evaluated
- [ ] Alertmanager receiving alerts
- [ ] Notification channels configured
- [ ] SLO dashboards created
- [ ] Weekly review scheduled
- [ ] Runbook documented

**You're ready for production monitoring! 🎉**
