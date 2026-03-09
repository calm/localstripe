# ADR: Namespace Isolation for Parallel Test Runs

**Status:** Accepted
**Date:** 2026-03-09

## Context

Localstripe uses a global in-memory dict (`Store`) as its database. When multiple test suites hit the same instance in parallel, they corrupt each other's state — list assertions break, mutations leak across suites, and webhook events fire into the wrong listeners.

The pickle-to-disk persistence (`/tmp/localstripe.pickle`) also creates an O(n) serialization bottleneck on every write.

## Decision

Partition all state by **API key namespace**. A key matching `sk_test_ns_{id}_key` routes to an isolated store partition. Standard keys like `sk_test_12345` use the `default` namespace, preserving backwards compatibility.

### Why API key (vs other approaches)

- **URL prefix** (`/{ns}/v1/...`) — Stripe SDKs set `host`/`port`/`protocol` separately with no path support. Would require SDK wrapper changes in every consumer.
- **Custom HTTP header** — Stripe SDKs don't support custom headers on every call without wrapping every method.
- **Multiple containers** — Higher memory cost, docker-compose complexity, and phases sharing an instance via modular arithmetic still collide.
- **API key** — Zero SDK changes. One-line client change (set the token). Mirrors how consumers already do database isolation.

### Implementation

1. **NamespacedStore** (`namespaced_store.py`) — dict-like class partitioned by `contextvars.ContextVar`. Seed data is frozen as a template and deep-copied on first namespace access.
2. **Namespace extraction** (`namespace_utils.py`) — parses `sk_test_ns_{id}_key` pattern, returns `'default'` for non-namespaced keys.
3. **Auth middleware** sets `current_namespace` contextvar before dispatching to handlers.
4. **Webhooks** (`webhooks.py`) scoped per namespace — registration and dispatch only within the same namespace.
5. **Cleanup endpoints** — `DELETE /_config/data/{namespace}` (single), `DELETE /_config/namespaces` (all).
6. **`--no-persist` flag** disables pickle serialization entirely.

## Consequences

**Positive:** Full isolation between parallel suites (store, webhooks, seed data). Eliminates pickle bottleneck. No changes to Stripe SDK call sites.

**Negative:** Memory increases ~1.5MB per namespace. Deep copy of template adds <100ms on first access per suite.

See the [README](../README.rst) for usage instructions.
