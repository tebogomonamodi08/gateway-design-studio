from __future__ import annotations

from nicegui import ui
from typing import Any, Callable


def header():
    with ui.row().classes('items-center justify-between w-full'):
        with ui.column():
            ui.label('AI Gateway Control Plane').classes('text-2xl title')
            ui.label('Configuration Management & Observability').classes('subtitle')
        with ui.row().classes('items-center gap-4'):
            ui.label('Offline Demo').classes('badge-healthy')


def upload_hero(on_upload: Callable[[bytes], Any]):
    """Render a full-width upload hero. Returns a callback handler attached to the native file input."""
    with ui.card().classes('w-full panel').style('display:flex;align-items:center;justify-content:center;padding:32px'):
        with ui.column().classes('items-center').style('gap:12px'):
            ui.html('<span aria-hidden="true" style="font-size:48px;color:var(--accent)">⬆️</span>')
            ui.label('Upload config.yaml').classes('text-2xl title')
            ui.label('Supports YAML • Max 5 MB').classes('muted')
            # Provide a simple choose-file button; client-side JS will handle posting
            btn = ui.button('Choose File', on_click=lambda: None).classes('neon-btn')
            # Invisible file input (controlled via JS in main.py)
            ui.html('<input id="fileInput" type="file" accept=".yaml,.yml" style="display:none">')
    return None


def config_card(config: dict | None, errors: list | None):
    card = ui.card().classes('w-96 panel')
    if config:
        with card:
            ui.label('Configuration').classes('text-lg')
            ui.separator()
            ui.label(f"Alias: {config.get('alias', '-')} ").classes('muted')
            ui.label(f"Provider: {config.get('provider', '-')} ").classes('muted')
            # model preview
            models = config.get('model_list', [])
            if models:
                m = models[0]
                ui.label(f"Model: {m.get('model_name')}").classes('muted')
                lp = m.get('litellm_params') or {}
                ui.label(f"Endpoint: {lp.get('api_base', '-')}").classes('muted')
            ui.label(f"Temperature: {config.get('temperature', '-')}").classes('muted')
            ui.label('Validated').classes('validated')
    elif errors:
        with card:
            ui.label('Configuration Invalid').classes('text-lg')
            ui.separator()
            for e in errors:
                with ui.card().classes('card-soft my-2'):
                    ui.label(e.get('loc')).classes('muted')
                    ui.label(e.get('msg')).classes('muted')
    else:
        with card:
            ui.label('No configuration uploaded').classes('muted')
    return card


def metrics_row(requests: int, latency_ms: int, success_pct: float):
    with ui.row().classes('gap-4'):
        with ui.card().classes('p-4 panel'):
            ui.label('Requests').classes('muted')
            ui.label(str(requests)).classes('metric-value')
        with ui.card().classes('p-4 panel'):
            ui.label('Latency').classes('muted')
            ui.label(f"{latency_ms} ms").classes('metric-value')
        with ui.card().classes('p-4 panel'):
            ui.label('Success').classes('muted')
            ui.label(f"{success_pct}%").classes('metric-value')


def node_card(name: str, status: str, on_click: Callable[[str], Any] | None = None):
    n = ui.card().classes('node')
    n.add(ui.label(name).classes('text-white'))
    n.add(ui.label(status).classes('muted'))
    if on_click:
        n.on('click', lambda *_: on_click(name))
    return n


def provider_panel(provider: dict):
    p = ui.card().classes('panel')
    with p:
        ui.label(f"Provider: {provider.get('name')}").classes('text-lg')
        ui.separator()
        ui.label(f"Status: {provider.get('status')}").classes('muted')
        ui.label(f"Latency: {provider.get('latency_ms')} ms").classes('muted')
        ui.label(f"Requests: {provider.get('requests')}").classes('muted')
        ui.label(f"Success: {int(provider.get('success_rate',0))}%").classes('muted')
    return p


def advisor_card(hints: list[str]):
    with ui.card().classes('panel'):
        ui.label('Gateway Advisor').classes('text-lg')
        ui.separator()
        for h in hints:
            ui.label(f"• {h}").classes('muted')


__all__ = [
    "header",
    "upload_hero",
    "config_card",
    "metrics_row",
    "node_card",
    "provider_panel",
    "advisor_card",
]

