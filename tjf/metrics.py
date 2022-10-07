from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics


def metrics_init_app(app: Flask):
    metrics = PrometheusMetrics.for_app_factory(
        metrics_endpoint="/metrics",
        # track metrics per route pattern, not per individual url
        group_by="url_rule",
    )

    metrics.init_app(app)
