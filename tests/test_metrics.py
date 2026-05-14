from app.infra.metrics import MetricsRegistry


def test_metrics_registry_renders_counters():
    metrics = MetricsRegistry()

    metrics.increment("http_requests_total", method="GET", path="/health", status="200")
    metrics.increment("http_requests_total", method="GET", path="/health", status="200")

    rendered = metrics.render_prometheus()

    assert 'http_requests_total{method="GET",path="/health",status="200"} 2' in rendered
