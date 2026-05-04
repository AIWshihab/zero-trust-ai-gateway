from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS


SECURITY_SUITE_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Security Test Suite</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui; --muted:#9ca8bd; --good:#34d399; --warn:#fbbf24; --bad:#fb7185; }
    body { margin:0; background:#050505; color:#f8fbff; }
    .shell { padding:18px; display:grid; gap:14px; }
    .row { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
    .card { border:1px solid rgba(255,255,255,.12); border-radius:16px; background:rgba(255,255,255,.05); padding:12px; }
    a,button { border:1px solid rgba(255,255,255,.15); border-radius:999px; padding:9px 12px; background:rgba(255,255,255,.06); color:#f8fbff; text-decoration:none; cursor:pointer; }
    input{ border:1px solid rgba(255,255,255,.15); border-radius:12px; background:rgba(0,0,0,.24); color:#f8fbff; padding:8px 10px; }
    .bar{ height:12px; border-radius:999px; background:rgba(255,255,255,.08); overflow:hidden; }
    .fill{ height:100%; width:0; background:linear-gradient(90deg,var(--good),var(--warn),var(--bad)); transition: width .28s ease; }
    .grid{ display:grid; grid-template-columns: repeat(3, minmax(160px,1fr)); gap:10px; }
    .muted{ color:var(--muted); font-size:12px; } .list{ display:grid; gap:8px; } .item{ border:1px solid rgba(255,255,255,.1); border-radius:12px; padding:8px; background:rgba(0,0,0,.22); }
  </style>
</head>
<body>
<main class="shell">
  <div class="row"><a href="/dashboard">Dashboard</a><a href="/control-plane">Control Plane</a></div>
  <h1 style="margin:0">Security Test Suite</h1>
  <article class="card">
    <div class="row"><label class="muted">Model ID <input id="modelId" type="number" value="1" min="1"/></label><button id="runBtn">Run Security Test Suite</button></div>
    <div class="bar" style="margin-top:10px"><div id="progress" class="fill"></div></div>
  </article>
  <article class="card">
    <div class="grid">
      <div><div class="muted">Detection Accuracy</div><strong id="acc">--</strong></div>
      <div><div class="muted">False Positive Rate</div><strong id="fpr">--</strong></div>
      <div><div class="muted">System Effectiveness</div><strong id="eff">--</strong></div>
    </div>
    <div id="results" class="list muted" style="margin-top:10px">No test run yet.</div>
  </article>
</main>
<script>
const api="/api/v1"; const token=sessionStorage.getItem("zta_token"); if(!token) location.href="/login?next=/dashboard/security";
const headers=()=>({Authorization:`Bearer ${token}`});
const req=async(path,opt={})=>{const res=await fetch(path,opt);const text=await res.text();let d={};try{d=text?JSON.parse(text):{}}catch{};if(!res.ok) throw new Error((d.detail&&d.detail.message)||d.detail||`Request failed (${res.status})`);return d;};
document.getElementById("runBtn").addEventListener("click", async ()=>{
  const modelId = Number(document.getElementById("modelId").value||1);
  const bar = document.getElementById("progress");
  const results = document.getElementById("results");
  bar.style.width = "10%"; results.textContent = "Executing security scenarios...";
  const ticker = setInterval(()=>{const w = Math.min(92, Number(bar.style.width.replace("%","")) + 11); bar.style.width = `${w}%`;}, 180);
  try {
    const data = await req(`${api}/security/test-suite?model_id=${modelId}`, { method: "POST", headers: headers() });
    clearInterval(ticker); bar.style.width = "100%";
    document.getElementById("acc").textContent = `${Math.round(Number(data.detection_accuracy||0)*100)}%`;
    document.getElementById("fpr").textContent = `${Math.round(Number(data.false_positive_rate||0)*100)}%`;
    document.getElementById("eff").textContent = `${Math.round(Number(data.system_effectiveness||0)*100)}%`;
    results.innerHTML = (data.results || []).map((r)=>`<div class="item"><strong>${r.passed ? "PASS" : "CHECK"}</strong> · expected ${r.expected}, got ${r.decision}<div class="muted" style="margin-top:4px">${r.prompt}</div></div>`).join("");
  } catch (e) {
    clearInterval(ticker); bar.style.width = "0%"; results.textContent = e.message;
  }
});
</script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
