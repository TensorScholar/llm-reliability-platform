 from __future__ import annotations

 from prometheus_client import Counter, Histogram


 requests_total = Counter(
     "api_requests_total", "Total API requests", labelnames=("route", "method", "status")
 )

 request_latency = Histogram(
     "api_request_latency_ms", "API request latency (ms)", buckets=(5, 10, 25, 50, 100, 250, 500, 1000)
 )


