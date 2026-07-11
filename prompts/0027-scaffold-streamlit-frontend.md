# Prompt Record 0027 — Scaffold Streamlit Frontend

## Date

2026-07-12

## Development goal

Create the Streamlit frontend foundation and verify communication with
the completed FastAPI backend.

## AI tool

ChatGPT

## Exact user prompt

> Now since you know the architecture of this project, how should I
> approach the frontend? Start from Step 1.

## Guidance summary

The frontend is implemented as a Streamlit presentation layer.

It does not directly access:

- SQLAlchemy models;
- PostgreSQL;
- backend service functions;
- synthetic-data loaders.

All frontend data is retrieved from FastAPI through a centralized HTTP
client.

The first frontend increment adds:

- a dedicated frontend directory;
- a centralized HTTPX backend client;
- environment-based FastAPI URL configuration;
- backend timeout and connection error handling;
- a Streamlit application shell;
- a visible synthetic-data and decision-support notice;
- a `/health` connectivity check;
- isolated HTTP-client tests.

The default local backend URL is:

```text
http://127.0.0.1:8000
```
