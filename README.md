# LLM Reliability Platform

Production monitoring and quality assurance for LLM applications. Provides ingestion, validation via invariants, drift detection, and querying APIs.

## Quickstart

1. Prerequisites: Docker and Docker Compose
2. Start stack:

```
make docker-up
```

API available at http://localhost:8000 (Docs at /docs)

## Services

- Platform API (FastAPI)
- TimescaleDB (PostgreSQL)
- Kafka (Confluent images)
- Redis

## Development

- Run API locally:

```
make api
```

- SDK (Python) lives under `LLM-REALIABILITY-PLATFORM/sdk/python`

## Environment

Copy and adapt environment variables as needed:

- `DATABASE__URL`
- `KAFKA__BOOTSTRAP_SERVERS`
- `REDIS__URL`
