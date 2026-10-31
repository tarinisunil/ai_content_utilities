# Deployment & Operations Guide

This guide describes how to configure, run, and scale the application across staging and production environments.

## Environment Variables

The system relies on the following environment configurations. Create a local `.env` file based on these keys:

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | String | `development` | Runtime mode (`development`, `staging`, `production`). |
| `PORT` | Integer | `8080` | The network port the server listens on. |
| `MAX_WORKERS` | Integer | `4` | The maximum number of concurrent processes. |
| `LOG_LEVEL` | String | `info` | Verbosity of output logs (`debug`, `info`, `warn`, `error`). |

## Local Deployment

### Using Docker (Recommended)

1. Build the production-ready image container:
   ```bash
   docker build -t app-core:latest .
   ```

2. Spin up the application with isolated environment variables:
   ```bash
   docker run -d -p 8080:8080 --env-file .env app-core:latest
   ```

## Production Deployment Checklist

Before deploying updates to production instances, ensure that:
* [ ] `APP_ENV` is explicitly set to `production`.
* [ ] Logging level (`LOG_LEVEL`) is dropped to `warn` or `error` to preserve disk IOPS.
* [ ] Health check endpoint (`/healthz`) responds with a `200 OK` status code.
* [ ] Memory usage alerts are active at a threshold of 80% usage.
