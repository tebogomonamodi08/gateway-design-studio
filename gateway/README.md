# AI Gateway Control Plane

Production-inspired internal tool demonstrating config upload, Pydantic validation, topology visualization, simulation, and advisor recommendations.

Architecture

- FastAPI serves JSON endpoints for uploads and simulation.
- NiceGUI provides a lightweight, modern UI that talks to the API via fetch() calls.
- Pydantic v2 is the trusted boundary for configuration validation.
- A simple in-memory topology simulates provider health and metrics.

Installation

1. Create a Python 3.10+ virtual environment.
2. Install dependencies:

```bash
python -m pip install -r gateway/requirements.txt
```

Running

```bash
python -m gateway.main
```

Open http://localhost:8080 in your browser.

5-minute Demo Walkthrough

1. Click the file input and upload a `config.yaml` (see example below).
2. Successful validation shows a green notification, a `Configuration` card, and the `Gateway Advisor` suggestions.
3. Topology updates and displays provider nodes; click a node to open the provider panel.
4. Use the simulation buttons (`Normal`, `Latency`, `Timeout`, `Failure`) to change provider state.
5. Explain the advisor hints and how the Gateway would reroute on failure.

Example `config.yaml`

```yaml
alias: demo-gateway
provider: primary
temperature: 1.3
model_list:
	- model_name: openai
		litellm_params:
			model: gpt4o
			api_base: https://example.openai.azure.com/
			api_key: fake-key
```

Notes

- This repo focuses on a vertical slice for demo purposes. The topology is in-memory and deterministic for presentation.
- See `engineering_notes.md` for architecture rationale and trade-offs.

