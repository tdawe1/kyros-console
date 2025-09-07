# Kyros – Agent Console & Orchestrator

Monorepo for the Kyros Agent Console (Next.js), Orchestrator (FastAPI), and local Terminal Daemon (node-pty).
Day-1 keeps DX fast (SQLite + in-proc bus) with clean interfaces so we can swap to Postgres/Redis/Temporal later.

## Console Authentication

### Development Setup
In development, set `NEXT_PUBLIC_DEV_BEARER` in your `.env.local` file:
```
NEXT_PUBLIC_DEV_BEARER="Bearer <paste-dev-token>"
```

### Production
In production, the Console should not carry tokens directly. Use a proper issuer or gateway for authentication.