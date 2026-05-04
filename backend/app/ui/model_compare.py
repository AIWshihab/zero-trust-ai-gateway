from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS


MODEL_COMPARE_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Model Compare</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui; --muted:#9ca8bd; --good:#34d399; --bad:#fb7185; --warn:#fbbf24; }
    body { margin:0; background:#050505; color:#f8fbff; }
    .shell { padding:18px; display:grid; gap:14px; }
    .row { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
    .card { border:1px solid rgba(255,255,255,.12); border-radius:16px; background:rgba(255,255,255,.05); padding:12px; }
    input, textarea { width:100%; border:1px solid rgba(255,255,255,.16); border-radius:12px; background:rgba(0,0,0,.25); color:#f8fbff; padding:9px; }
    a,button { border:1px solid rgba(255,255,255,.15); border-radius:999px; padding:9px 12px; background:rgba(255,255,255,.06); color:#f8fbff; text-decoration:none; cursor:pointer; }
    .results { display:grid; grid-template-columns: repeat(auto-fit, minmax(280px,1fr)); gap:10px; }
    .badge { border:1px solid rgba(255,255,255,.16); border-radius:999px; padding:3px 7px; font-size:11px; }
    .allow{color:var(--good);} .challenge{color:var(--warn);} .block{color:var(--bad);}
    .muted{color:var(--muted); font-size:12px;}
    pre{white-space:pre-wrap;word-break:break-word;background:rgba(0,0,0,.24);border:1px solid rgba(255,255,255,.1);border-radius:12px;padding:8px;}
  </style>
</head>
<body>
<main class="shell">
  <div class="row"><a href="/dashboard">Dashboard</a><a href="/chat">Chat</a></div>
  <h1 style="margin:0">Model Security Comparison</h1>
  <article class="card">
    <label class="muted">Model IDs (comma separated)</label>
    <input id="modelIds" value="1" />
    <label class="muted" style="margin-top:8px">Prompt</label>
    <textarea id="prompt" rows="4">Explain zero trust architecture in plain language.</textarea>
    <div class="row" style="margin-top:8px"><button id="runBtn">Compare</button></div>
  </article>
  <article class="card">
    <div class="muted">Safest and riskiest labels are computed from returned effective risk.</div>
    <div id="results" class="results muted">No comparison yet.</div>
  </article>
</main>
<script>
const api="/api/v1"; const token=sessionStorage.getItem("zta_token"); if(!token) location.href="/login?next=/dashboard/models/compare";
const headers=()=>({Authorization:`Bearer ${token}`,"Content-Type":"application/json"});
const req=async(path,opt={})=>{const res=await fetch(path,opt);const text=await res.text();let d={};try{d=text?JSON.parse(text):{}}catch{};if(!res.ok) throw new Error((d.detail&&d.detail.message)||d.detail||`Request failed (${res.status})`);return d;};
function cls(decision){const d=String(decision||"").toLowerCase(); return d.includes("block")?"block":d.includes("challenge")?"challenge":"allow";}
function esc(v){return String(v??"").replace(/[&<>\"']/g,(c)=>({"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#039;"}[c]));}
document.getElementById("runBtn").addEventListener("click", async () => {
  const ids = document.getElementById("modelIds").value.split(",").map((x)=>Number(x.trim())).filter(Boolean);
  const prompt = document.getElementById("prompt").value.trim();
  if (!ids.length || !prompt) return;
  const out = document.getElementById("results");
  out.textContent = "Running comparison...";
  const data = await req(`${api}/security/models/compare`, { method:"POST", headers: headers(), body: JSON.stringify({ model_ids: ids, prompt, parameters: { temperature: 0.2, max_tokens: 700 }})});
  const rows = data.results || [];
  const sorted = [...rows].sort((a,b)=>Number(a.effective_risk||0)-Number(b.effective_risk||0));
  const safest = sorted[0]?.model_id;
  const riskiest = sorted[sorted.length-1]?.model_id;
  out.innerHTML = rows.map((r)=>`<article class="card"><div class="row"><strong>Model ${r.model_id}</strong><span class="badge ${cls(r.decision)}">${r.decision}</span>${r.model_id===safest?`<span class="badge allow">safest</span>`:""}${r.model_id===riskiest?`<span class="badge block">highest risk</span>`:""}</div><div class="muted">effective risk ${Number(r.effective_risk||0).toFixed(3)} · security ${Number(r.security_score||0).toFixed(3)}</div><pre>${esc(r.output||"No output")}</pre><div class="muted">${esc(r.explanation||r.reason||"")}</div></article>`).join("");
}).catch((e)=>{document.getElementById("results").textContent=e.message;});
</script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
