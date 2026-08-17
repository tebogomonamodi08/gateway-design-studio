from __future__ import annotations

from nicegui import ui, app
from fastapi import UploadFile
from fastapi import APIRouter

try:
    from .parser import parse_and_validate
    from .advisor import advise
    from .topology import DEFAULT
    from .components import header, upload_hero, config_card, metrics_row, node_card, provider_panel, advisor_card
except Exception:
    from parser import parse_and_validate
    from advisor import advise
    from topology import DEFAULT
    from components import header, upload_hero, config_card, metrics_row, node_card, provider_panel, advisor_card

from typing import Any


api = APIRouter()


def _snapshot_providers() -> list[dict[str, Any]]:
    snapshot = []
    for p in DEFAULT.get_snapshot():
        snapshot.append({
            "name": p.name,
            "status": p.status,
            "requests": p.requests,
            "latency_ms": p.latency_ms,
            "success_rate": p.success_rate,
            "last_check": p.last_check,
        })
    return snapshot


@api.post('/upload')
async def upload_config(file: UploadFile):
    body = await file.read()
    cfg, errors = parse_and_validate(body)
    if cfg:
        for item in cfg.model_list:
            DEFAULT.add_provider(item.model_name)
        hints = advise(cfg)
        return {"ok": True, "config": cfg.model_dump(), "hints": hints, "providers": _snapshot_providers()}
    else:
        return {"ok": False, "errors": errors}


@api.post('/simulate')
async def simulate_event(payload: dict):
    provider = payload.get('provider')
    mode = payload.get('mode')
    if provider and mode:
        DEFAULT.simulate(provider, mode)
        return {"ok": True, "providers": _snapshot_providers()}
    return {"ok": False, "msg": "invalid payload"}


@api.get('/providers')
async def get_providers():
    return {"providers": _snapshot_providers()}


def _render_page():
    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1">')
    ui.add_head_html("""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#05060a; --panel:#071326; --muted:#9CA3AF; --accent:#0ea5ff; --accent-strong:#60a5fa;
}
html,body{height:100%;background:var(--bg);font-family:Inter, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;color:#fff}
.panel{background:var(--panel);border-radius:10px;padding:12px}
.card-soft{background:transparent;border-radius:10px;padding:12px;border:1px solid rgba(255,255,255,0.03)}
.badge-healthy{background:#10b981;color:white;padding:6px 10px;border-radius:6px}
.validated{background:#059669;color:white;padding:6px 10px;border-radius:6px}
.neon-btn{background:transparent;color:var(--accent);border:1px solid rgba(14,165,255,0.25);padding:8px 10px;border-radius:8px;cursor:pointer}
.neon-btn:hover{box-shadow:0 0 16px rgba(14,165,255,0.18);background:rgba(14,165,255,0.03)}
.node{border:2px solid var(--accent);border-radius:12px;padding:12px;background:#051525;color:white;width:200px;cursor:pointer}
.node:hover{box-shadow:0 0 18px rgba(14,165,255,0.14)}
.muted{color:var(--muted)}
.title{font-weight:300}
.subtitle{color:var(--muted);font-size:0.9rem}
.metric-value{font-size:1.5rem;font-weight:300}
</style>
""")
    ui.run_javascript("document.documentElement.style.background='var(--bg)'")
    header()

    # Upload hero
    upload_hero(None)

    # Placeholders
    ui.html('<div id="cfg" style="margin-top:18px"></div>')
    ui.html('<div id="advisor" style="margin-top:12px"></div>')
    ui.html('<div id="topo" style="display:flex;gap:12px;flex-wrap:wrap;margin-top:12px"></div>')
    ui.html('<div id="providerPanel" style="margin-top:12px"></div>')

    # Metrics
    metrics_row(12, 612, 98)

    # Wire client-side upload behavior using a small amount of JS for file input
    ui.run_javascript('''
const fileInput = document.getElementById('fileInput');
// wire the visible Choose File button to the hidden input
const chooseBtn = document.querySelector('.neon-btn');
if (chooseBtn && fileInput) {
  chooseBtn.addEventListener('click', ()=>fileInput.click());
}
fileInput?.addEventListener('change', async function(e) {
  const f = e.target.files[0];
  if (!f) return;
  const fd = new FormData(); fd.append('file', f);
  const statusEl = document.getElementById('cfg');
  statusEl.innerHTML = '<div class="panel">Uploading and validating...</div>';
  const res = await fetch('/upload', { method: 'POST', body: fd });
  const data = await res.json();
  if (data.ok) {
    // render configuration
    const cfg = data.config;
    document.getElementById('cfg').innerHTML = `<div class="panel"><h3 class='title'>Configuration</h3>
      <div class='muted'>Alias: ${cfg.alias || '-'}<br/>Provider: ${cfg.provider || '-'}<br/>Temperature: ${cfg.temperature}</div></div>`;
    // advisor
    const adv = document.getElementById('advisor');
    adv.innerHTML = `<div class="panel"><h4 class='title'>Gateway Advisor</h4><ul class='muted'>${data.hints.map(h => '<li>' + h.message + '</li>').join('')}</ul></div>`;
    // topology
    const topo = document.getElementById('topo'); topo.innerHTML = '';
    (data.providers||[]).forEach(p=>{
      const n = document.createElement('div');
      n.className = 'node';
      n.innerHTML = `<strong>${p.name}</strong><div class='muted'>${p.status}</div>`;
      n.onclick = async ()=>{
        // fetch latest providers
        const resp = await fetch('/providers');
        const snap = await resp.json();
        const prov = (snap.providers||[]).find(x=>x.name===p.name)||p;
        document.getElementById('providerPanel').innerHTML = `<div class="panel"><h4 class='title'>Provider: ${prov.name}</h4>
          <div class='muted'>Status: ${prov.status}<br/>Latency: ${prov.latency_ms} ms<br/>Requests: ${prov.requests}<br/>Success: ${Math.round(prov.success_rate)}%</div>
          <div style="margin-top:8px"><button class='neon-btn' onclick="(async()=>{await fetch('/simulate',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({provider:'${p.name}',mode:'normal'})});location.reload();})()">Normal</button>
          <button class='neon-btn' onclick="(async()=>{await fetch('/simulate',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({provider:'${p.name}',mode:'latency'})});location.reload();})()">Latency</button>
          <button class='neon-btn' onclick="(async()=>{await fetch('/simulate',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({provider:'${p.name}',mode:'timeout'})});location.reload();})()">Timeout</button>
          <button class='neon-btn' onclick="(async()=>{await fetch('/simulate',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({provider:'${p.name}',mode:'failure'})});location.reload();})()">Failure</button></div></div>`;
      };
      topo.appendChild(n);
    });
  } else {
    const errs = data.errors||[];
    document.getElementById('cfg').innerHTML = `<div class='panel'><h3 class='title'>Configuration Invalid</h3><div class='muted'>Fix highlighted fields</div>${errs.map(e=>`<div class='card-soft' style='margin-top:8px;padding:8px'><strong>${e.loc}</strong><div class='muted'>${e.msg}</div></div>`).join('')}</div>`;
  }
});
''')


def create_ui():
    @ui.page('/')
    def _index():
        _render_page()

    # mount API router and run
    app.include_router(api)
    ui.run(host='0.0.0.0', port=8080)


if __name__ in {"__main__", "__mp_main__"}:
    create_ui()
