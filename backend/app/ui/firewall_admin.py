from app.ui.common import CYBER_UI_CSS, CYBER_UI_JS


FIREWALL_ADMIN_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Firewall Clients</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui; --muted:#9ca8bd; }
    body { margin:0; background:#050505; color:#f8fbff; }
    .shell { padding: 18px; display:grid; gap:14px; }
    .row { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
    .grid { display:grid; grid-template-columns: 340px 1fr; gap:14px; }
    .card { border:1px solid rgba(255,255,255,.12); border-radius:16px; padding:12px; background:rgba(255,255,255,.05); }
    label { display:grid; gap:6px; font-size:12px; color:var(--muted); }
    input, select { border:1px solid rgba(255,255,255,.15); border-radius:12px; background:rgba(0,0,0,.24); color:#f8fbff; padding:8px 10px; }
    a, button { border:1px solid rgba(255,255,255,.15); border-radius:999px; padding:9px 12px; background:rgba(255,255,255,.06); color:#f8fbff; text-decoration:none; cursor:pointer; }
    .list { display:grid; gap:10px; }
    .item { border:1px solid rgba(255,255,255,.1); border-radius:12px; padding:10px; background:rgba(0,0,0,.2); transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease; }
    .item:hover { transform: translateY(-2px); border-color: rgba(34,211,238,.45); box-shadow: 0 0 20px rgba(34,211,238,.12); }
    .muted { color: var(--muted); font-size:12px; }
    pre { white-space:pre-wrap; word-break:break-word; background:rgba(0,0,0,.28); border:1px solid rgba(255,255,255,.1); border-radius:12px; padding:8px; }
    @media (max-width: 980px){ .grid{grid-template-columns:1fr;} }
  </style>
</head>
<body>
<main class="shell">
  <section class="row"><a href="/dashboard">Dashboard</a><a href="/control-plane">Control Plane</a><button id="refreshBtn">Refresh</button></section>
  <h1 style="margin:0">Firewall Client Admin</h1>
  <section class="grid">
    <article class="card">
      <h3 style="margin:4px 0 10px">Create / Update Client</h3>
      <div class="list">
        <label>Client ID<input id="client_id" placeholder="partner-app"/></label>
        <label>Name<input id="name" placeholder="Partner App"/></label>
        <label>API key<input id="api_key" placeholder="leave blank to auto-generate"/></label>
        <label>Rate limit<input id="rate_limit" type="number" value="60" min="1"/></label>
        <label>Window seconds<input id="rate_window_seconds" type="number" value="60" min="1"/></label>
        <label>Trust score<input id="trust_score" type="number" value="0.8" min="0" max="1" step="0.01"/></label>
        <label>Require signature<select id="require_signature"><option value="false">false</option><option value="true">true</option></select></label>
        <label>HMAC secret<input id="hmac_secret"/></label>
        <div class="row"><button id="saveBtn">Save</button><button id="resetBtn">Reset</button></div>
      </div>
      <pre id="newKey" class="muted">Generated keys will appear here once after create/update.</pre>
    </article>
    <article class="card">
      <h3 style="margin:4px 0 10px">Clients</h3>
      <div id="clients" class="list muted">Loading…</div>
    </article>
  </section>
</main>
<script>
const api="/api/v1"; const token=sessionStorage.getItem("zta_token"); if(!token) location.href="/login?next=/dashboard/firewall";
const headers=()=>({Authorization:`Bearer ${token}`,"Content-Type":"application/json"});
let editing=null;
const $=(id)=>document.getElementById(id);
const req=async(path,opt={})=>{const res=await fetch(path,opt);const text=await res.text();let d={};try{d=text?JSON.parse(text):{}}catch{};if(!res.ok) throw new Error((d.detail&&d.detail.message)||d.detail||`Request failed (${res.status})`);return d;};
const mask=(value)=>{const v=String(value||"");return v.length<=4?"****":`****${v.slice(-4)}`;};
const usage=(c)=>c.usage_count ?? c.request_count ?? c.total_requests ?? 0;
function fill(c){editing=c.client_id;$("client_id").value=c.client_id;$("client_id").disabled=true;$("name").value=c.name;$("api_key").value="";$("rate_limit").value=c.rate_limit;$("rate_window_seconds").value=c.rate_window_seconds;$("trust_score").value=c.trust_score;$("require_signature").value=String(!!c.require_signature);$("hmac_secret").value="";}
function resetForm(){editing=null;$("client_id").disabled=false;["client_id","name","api_key","hmac_secret"].forEach((id)=>$(id).value="");$("rate_limit").value=60;$("rate_window_seconds").value=60;$("trust_score").value=0.8;$("require_signature").value="false";}
async function load(){const rows=await req(`${api}/firewall/clients`,{headers:headers()});$("clients").innerHTML=rows.map(c=>`<div class="item"><div class="row"><strong>${c.client_id}</strong><span class="muted">${c.name}</span></div><div class="muted">rate ${c.rate_limit}/${c.rate_window_seconds}s · trust ${Number(c.trust_score).toFixed(2)} · usage ${usage(c)} · key ${mask(c.api_key || "")}</div><div class="row" style="margin-top:8px"><button onclick='window.__edit("${c.client_id}")'>Edit</button><button onclick='window.__toggle("${c.client_id}",${!c.is_active})'>${c.is_active?"Disable":"Enable"}</button><button onclick='window.__copyMasked("${c.client_id}")'>Copy ID</button><button onclick='window.__regen("${c.client_id}")'>Regenerate key</button></div></div>`).join("")||"No clients";}
window.__edit=async(id)=>{const rows=await req(`${api}/firewall/clients`,{headers:headers()});const c=rows.find(x=>x.client_id===id);if(c) fill(c);};
window.__toggle=async(id,active)=>{await req(`${api}/firewall/clients/${encodeURIComponent(id)}`,{method:"PATCH",headers:headers(),body:JSON.stringify({is_active:active})});await load();};
window.__copyMasked=async(id)=>{try{await navigator.clipboard.writeText(id);$("newKey").textContent=`Copied client ID: ${id}`;}catch{$("newKey").textContent="Clipboard unavailable in this browser context.";}};
window.__regen=async(id)=>{if(!confirm(`Regenerate API key for ${id}? Existing integrations must update keys.`)) return;const key=`gw_${Math.random().toString(36).slice(2)}${Math.random().toString(36).slice(2)}`;const d=await req(`${api}/firewall/clients/${encodeURIComponent(id)}`,{method:"PATCH",headers:headers(),body:JSON.stringify({api_key:key})});$("newKey").textContent=d.api_key?`New key for ${d.client_id}: ${d.api_key}`:"Key regenerated.";await load();};
$("saveBtn").addEventListener("click",async()=>{const body={client_id:$("client_id").value,name:$("name").value,api_key:$("api_key").value||null,rate_limit:Number($("rate_limit").value),rate_window_seconds:Number($("rate_window_seconds").value),trust_score:Number($("trust_score").value),require_signature:$("require_signature").value==="true",hmac_secret:$("hmac_secret").value||null,is_active:true};const path=editing?`${api}/firewall/clients/${encodeURIComponent(editing)}`:`${api}/firewall/clients`;if(editing) delete body.client_id;const d=await req(path,{method:editing?"PATCH":"POST",headers:headers(),body:JSON.stringify(body)});$("newKey").textContent=d.api_key?`New key for ${d.client_id}: ${d.api_key}`:"Saved.";await load();});
$("resetBtn").addEventListener("click",resetForm);$("refreshBtn").addEventListener("click",()=>load().catch(e=>alert(e.message)));load().catch(e=>{$("clients").textContent=e.message;});
</script>
</body>
</html>
""".replace("</style>", f"{CYBER_UI_CSS}\n  </style>").replace("</body>", f"{CYBER_UI_JS}\n</body>")
