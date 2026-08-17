# Engineering Notes

## System Boundaries

- Trusted boundary: Pydantic `GatewayConfig` (see [gateway/models.py](gateway/models.py)). All untrusted YAML is parsed with `yaml.safe_load()` and immediately validated by Pydantic.
- Untrusted inputs: uploaded YAML bytes and any UI client payloads. The server enforces structure and types before acting.

## Why Pydantic

- Pydantic v2 is used as the canonical validation and data transformation layer. It provides clear error messages and serves as the source of truth for downstream logic (topology population, routing decisions).

## Architecture

```mermaid
flowchart TD
	Browser -->|upload YAML| FastAPI[/FastAPI\n(upload endpoint)/]
	FastAPI --> Parser[Parser & Pydantic]
	Parser -->|valid| Topology[In-memory Topology]
	Topology --> UI(NiceGUI)
	Parser -->|hints| Advisor[Advisor Rules Engine]
	UI -->|simulate| FastAPI
```

## Module Responsibilities

- `models.py`: Pydantic models representing the LiteLLM config and GatewayConfig.
- `parser.py`: YAML parsing and validation helpers; returns structured errors for UI display.
- `advisor.py`: Lightweight rules engine for human-friendly recommendations.
- `topology.py`: In-memory simulation of provider state; single responsibility for provider lifecycle and metrics.
- `components.py`: NiceGUI UI building blocks (header, cards, metrics).
- `main.py`: Glue layer wiring API + UI. Minimal server-side logic; UI-driven interactions use `/upload` and `/simulate`.

## Trade-offs

- Simplicity vs completeness: The topology is intentionally simple and in-memory to keep the demo focused and deterministic.
- No persistence: For a production system, persist configs and metrics to a database and use long-running background tasks for health checks.
- Security: CORS is permissive for the demo. In prod, restrict origins and enforce authentication and rate-limiting.

## Future Improvements

- Add authentication (OAuth2 / mTLS) for internal tooling.
- Persist configurations and provide versioning and rollbacks.
- Integrate real health checks and time-series metrics (Prometheus/Grafana).
- Add a real routing layer that supports circuit-breaking and retries.

System boundaries, trusted vs untrusted, Pydantic rationale, architecture diagram, trade-offs, and future improvements.

See included `models.py` for the trusted schema and `parser.py` for validation boundary.
