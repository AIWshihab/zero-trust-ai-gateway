import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

// ══════════════════════════════════════════════════════════════════════════════
//  NODE + EDGE DATA
// ══════════════════════════════════════════════════════════════════════════════
const NODES = [
  { id:'core',       label:'Gateway Core',   color:0x3b0fa8, emissive:0x1a0560, glow:0x8b5cf6, pos:[0,0,0],         size:1.5,  sub:'Central routing hub' },
  { id:'auth',       label:'Auth Engine',    color:0x1e3a8a, emissive:0x0c1a4a, glow:0x60a5fa, pos:[-5.5,1.5,0],    size:0.88, sub:'JWT & RBAC' },
  { id:'prompt',     label:'Prompt Guard',   color:0x0c4a6e, emissive:0x082f49, glow:0x38bdf8, pos:[-2.8,0.2,4],    size:0.88, sub:'Input scanning' },
  { id:'policy',     label:'Policy Engine',  color:0x4c1d95, emissive:0x2e1065, glow:0xa78bfa, pos:[0,2.8,1.8],     size:1.0,  sub:'Zero-trust scoring' },
  { id:'firewall',   label:'AI Firewall',    color:0x7f1d1d, emissive:0x450a0a, glow:0xf87171, pos:[3,0,4],          size:1.0,  sub:'Adaptive PEP' },
  { id:'models',     label:'AI Models',      color:0x064e3b, emissive:0x022c22, glow:0x34d399, pos:[5.8,1.5,0],     size:1.0,  sub:'HuggingFace pool' },
  { id:'output',     label:'Output Guard',   color:0x78350f, emissive:0x431407, glow:0xfbbf24, pos:[4,-1.8,-1.5],   size:0.82, sub:'Response filtering' },
  { id:'registry',   label:'Model Registry', color:0x3b0764, emissive:0x1e0538, glow:0xd8b4fe, pos:[4.2,3.8,-2],    size:0.78, sub:'Model catalog' },
  { id:'detection',  label:'Detection',      color:0x7c2d12, emissive:0x431407, glow:0xfb923c, pos:[1,-2.8,3],      size:0.78, sub:'Threat detection' },
  { id:'assessment', label:'Assessment',     color:0x1e1b4b, emissive:0x0f0b2e, glow:0xc4b5fd, pos:[-2.2,3.2,-2.2],size:0.78, sub:'OWASP LLM posture' },
  { id:'monitoring', label:'Monitoring',     color:0x0c4a6e, emissive:0x042e44, glow:0x67e8f9, pos:[0,-3.8,-0.8],   size:0.88, sub:'Real-time metrics' },
  { id:'evaluation', label:'Evaluation',     color:0x831843, emissive:0x500724, glow:0xf9a8d4, pos:[-4.2,2.8,-3.2], size:0.78, sub:'Research suite' },
];
const EDGES = [
  ['core','auth'],['core','prompt'],['core','policy'],['core','firewall'],
  ['core','models'],['core','monitoring'],['auth','prompt'],
  ['prompt','policy'],['policy','firewall'],['firewall','models'],
  ['models','output'],['output','core'],['models','registry'],
  ['policy','detection'],['policy','assessment'],['firewall','detection'],
  ['evaluation','models'],['assessment','core'],['monitoring','detection'],['monitoring','core'],
];
const nodeMap = {};
NODES.forEach(n => nodeMap[n.id] = n);

// ══════════════════════════════════════════════════════════════════════════════
//  ACTIVITY FEEDS
// ══════════════════════════════════════════════════════════════════════════════
const FEEDS = {
  core:       [['info','ROUTE → /api/v1/chat → auth✓ prompt✓ policy✓ firewall✓ → models'],['ok','ZTA_ENFORCE → trust:0.84 ALLOW [12ms]'],['info','ROUTE → /api/v1/models → auth✓ admin✓ → registry'],['warn','ROUTE → /api/v1/gateway → trust:0.52 CHALLENGE'],['ok','GATEWAY → 847 requests processed since startup'],['bad','BLOCK → /api/v1/chat injection risk:0.91'],['ok','HEALTH → All 12 subsystems nominal'],['info','ROUTE → /api/v1/detect → auth✓ → detection engine']],
  auth:       [['ok','TOKEN_ISSUED → user:admin [exp:30min] [HS256]'],['ok','TOKEN_VALID → user:analyst [remaining:18min]'],['warn','TOKEN_EXPIRED → user:testbot [session closed]'],['ok','LOGIN_OK → user:admin [127.0.0.1] [RBAC:admin]'],['ok','TOKEN_ISSUED → user:viewer [exp:30min]'],['bad','LOGIN_FAIL → user:unknown [3 attempts] [locked]'],['ok','TOKEN_REFRESH → user:analyst [rotated]'],['info','SESSION_START → user:admin [JWT issued]']],
  prompt:     [['ok','SCAN:CLEAN → "What are the latest AI safety papers?"'],['bad','SCAN:INJECT → [BLOCKED] "Ignore previous instructions and…"'],['warn','SCAN:PII → [REDACT] SSN detected in prompt'],['ok','SCAN:CLEAN → "Summarise this research paper"'],['bad','SCAN:JAILBREAK → [BLOCKED] DAN persona attempt'],['ok','SCAN:CLEAN → "How does zero-trust architecture work?"'],['bad','SCAN:ADVERSARIAL → Repetitive probing pattern detected'],['ok','SCAN:CLEAN → "List the OWASP LLM Top 10"']],
  policy:     [['ok','DECISION:ALLOW → risk:0.22 [model:0.20|data:0.10|prompt:0.05|rate:0.02]'],['bad','DECISION:BLOCK → risk:0.91 [prompt:0.65|model:0.18|rate:0.08]'],['warn','DECISION:CHALLENGE → risk:0.52 [rate:0.28|penalty:0.15]'],['ok','SCORE → composite:0.34 threshold:0.75 → ALLOW'],['info','WEIGHTS → model:0.25 data:0.20 prompt:0.30 rate:0.15 trust:0.10'],['ok','DECISION:ALLOW → risk:0.29 all weights nominal'],['info','POLICY_RELOAD → config refreshed from settings'],['bad','DECISION:BLOCK → risk:0.95 critical injection risk']],
  firewall:   [['ok','ALLOW → client:web-app sig:valid trust:0.84 [8ms]'],['bad','BLOCK → client:unknown no API key [rate exceeded]'],['warn','CHALLENGE → client:mobile trust:0.51 [CAPTCHA]'],['ok','HMAC_VALID → client:default-client sig verified'],['warn','RATE_LIMIT → client:testbot 100/min exceeded'],['ok','ALLOW → client:web-app trust:0.91 [12ms]'],['info','CLIENT_REGISTERED → new:dashboard key issued'],['bad','BLOCK → client:scraper injection payload detected']],
  models:     [['ok','INFER → Llama-3.1-8B prompt:42tok resp:128tok 1.2s'],['ok','INFER → Qwen3-1.7B prompt:18tok resp:64tok 0.8s'],['ok','INFER → Mistral-7B prompt:55tok resp:192tok 1.5s'],['ok','HEALTH → All 3 HF models responding normally'],['info','HF_ROUTER → featherless-ai latency:320ms'],['ok','INFER → Llama-3.1-8B prompt:28tok SAFE 0.9s'],['info','TOKEN_USAGE → Llama:2.4k Qwen:1.1k Mistral:3.2k'],['ok','ROUTE → Policy selected: Mistral-7B [risk:LOW]']],
  output:     [['ok','OUTPUT:CLEAN → Response passed all content checks'],['warn','OUTPUT:REDACT → [PII_EMAIL] removed from response'],['bad','OUTPUT:BLOCK → [POLICY_VIOLATION] suppressed'],['ok','OUTPUT:CLEAN → Code snippet safe to deliver'],['warn','OUTPUT:REDACT → [PHONE_NUMBER] masked in output'],['ok','OUTPUT:CLEAN → Research summary delivered'],['warn','OUTPUT:FLAG → [SENSITIVE_TOPIC] passed with warning'],['warn','OUTPUT:REDACT → [CREDENTIALS] detected and removed']],
  registry:   [['ok','SCAN → meta-llama/Llama-3.1-8B → protected'],['ok','CHECK → Qwen/Qwen3-1.7B posture:PASS 9/10'],['info','UPDATE → Mistral-7B risk score recalculated: 0.24'],['ok','QUERY → Model list requested by policy engine'],['ok','POSTURE → All 4 models protected'],['ok','SCAN → meta-llama/Meta-Llama-3-8B → protected'],['info','SYNC → 4 models registered 4 active'],['ok','RISK → Llama:0.22 Qwen:0.18 Mistral:0.24 Llama-3:0.21']],
  detection:  [['bad','MATCH → [INJECTION] pattern:ignore_previous in prompt'],['ok','CLEAN → No threat patterns in request'],['bad','MATCH → [JAILBREAK] DAN persona detected'],['warn','MATCH → [PII] SSN pattern found in input'],['bad','SEQ → Attack sequence: probe→inject→exfil'],['ok','CLEAN → Research query: no threats'],['bad','MATCH → [ADVERSARIAL] Repetitive probing detected'],['warn','COUNT → 12 threats blocked in last 60s']],
  assessment: [['ok','LLM01 → Prompt Injection: PASS controls active'],['ok','LLM02 → Insecure Output: PASS output guard on'],['info','LLM03 → Training Poisoning: N/A'],['ok','LLM04 → Model DoS: PASS rate limiting active'],['warn','LLM05 → Supply Chain: WARN review HF provenance'],['ok','LLM06 → Sensitive Info: PASS PII redaction on'],['info','LLM07 → Insecure Plugin: N/A'],['ok','LLM08 → Excessive Agency: PASS firewall enforced'],['warn','LLM09 → Overreliance: WARN user guidance needed'],['ok','LLM10 → Model Theft: PASS auth required']],
  monitoring: [['ok','REQ_ALLOW → /api/v1/chat trust:0.82 [12ms]'],['bad','REQ_BLOCK → /api/v1/models risk:0.91 [injection]'],['warn','REQ_CHALLENGE → /api/v1/gateway trust:0.55'],['info','METRIC_SYNC → 847 total requests logged'],['warn','ALERT → Block rate exceeded 25% threshold'],['ok','REQ_ALLOW → /api/v1/auth trust:0.94 [8ms]'],['info','LOG_FLUSH → 1,204 entries written'],['bad','REQ_BLOCK → /api/v1/gateway risk:0.88 jailbreak']],
  evaluation: [['info','EVAL → adversarial_prompts_v2 [running]'],['ok','PASS → test_injection_basic 8/8 blocked'],['ok','PASS → test_pii_detection 12/12 redacted'],['bad','FAIL → test_jailbreak_advanced 2/10 bypassed'],['info','BENCH → latency avg:1.1s p99:2.4s'],['ok','PASS → test_auth_bypass 0 vulnerabilities'],['ok','SCORE → Security posture: 87/100'],['ok','COMPLETE → Suite 94% pass rate']],
};

// ══════════════════════════════════════════════════════════════════════════════
//  METRIC TEMPLATES
// ══════════════════════════════════════════════════════════════════════════════
const METRIC_DEFS = {
  core:       [{k:'Gateway Status',v:'Online',cls:'good',pct:100},{k:'ZTA Mode',v:'Strict',cls:'good',pct:100},{k:'Subsystems',v:'12 / 12',cls:'good',pct:100},{k:'Total Requests',v:'live:total_requests',cls:'',pct:null}],
  auth:       [{k:'Active Sessions',v:'live:sessions',cls:'good',pct:null},{k:'Algorithm',v:'HS256',cls:'',pct:null},{k:'Token TTL',v:'30 min',cls:'',pct:null},{k:'Failed Logins',v:'3',cls:'warn',pct:null}],
  prompt:     [{k:'Scans Today',v:'live:total_requests',cls:'good',pct:null},{k:'Threats Blocked',v:'live:blocked_requests',cls:'bad',pct:null},{k:'PII Detected',v:'4',cls:'warn',pct:null},{k:'Clean Rate',v:'live:clean_pct',cls:'good',pct:null}],
  policy:     [{k:'Block Threshold',v:'0.75',cls:'',pct:75},{k:'Challenge At',v:'0.50',cls:'warn',pct:50},{k:'Avg Risk Score',v:'0.34',cls:'good',pct:34},{k:'Decisions Today',v:'live:total_requests',cls:'',pct:null}],
  firewall:   [{k:'Requests Allowed',v:'live:allowed_requests',cls:'good',pct:null},{k:'Requests Blocked',v:'live:blocked_requests',cls:'bad',pct:null},{k:'Rate Limit',v:'100 / min',cls:'',pct:null},{k:'Active Clients',v:'live:clients',cls:'good',pct:null}],
  models:     [{k:'Active Models',v:'live:active',cls:'good',pct:null},{k:'Protected',v:'live:protected',cls:'good',pct:null},{k:'Provider',v:'HuggingFace',cls:'',pct:null},{k:'Avg Latency',v:'1.1 s',cls:'good',pct:null}],
  output:     [{k:'Responses Clean',v:'94 %',cls:'good',pct:94},{k:'PII Redacted',v:'6 %',cls:'warn',pct:6},{k:'Content Blocked',v:'2 %',cls:'bad',pct:2},{k:'Filter Mode',v:'Strict',cls:'good',pct:null}],
  registry:   [{k:'Registered',v:'live:registered',cls:'',pct:null},{k:'Protected',v:'live:protected',cls:'good',pct:null},{k:'Posture Engine',v:'Running',cls:'good',pct:null},{k:'Framework',v:'OWASP LLM',cls:'',pct:null}],
  detection:  [{k:'Active Rules',v:'live:rules',cls:'good',pct:null},{k:'Threats Today',v:'live:blocked_requests',cls:'bad',pct:null},{k:'Attack Sequences',v:'3',cls:'warn',pct:null},{k:'Engine',v:'Pattern Match',cls:'',pct:null}],
  assessment: [{k:'Controls',v:'10 / OWASP LLM',cls:'',pct:100},{k:'Overall Score',v:'87 / 100',cls:'good',pct:87},{k:'PASS',v:'8 / 10',cls:'good',pct:80},{k:'WARN',v:'2 / 10',cls:'warn',pct:20}],
  monitoring: [{k:'Total Requests',v:'live:total_requests',cls:'',pct:null},{k:'Blocked',v:'live:blocked_requests',cls:'bad',pct:null},{k:'Block Rate',v:'live:block_rate',cls:'warn',pct:null},{k:'Allowed',v:'live:allowed_requests',cls:'good',pct:null}],
  evaluation: [{k:'Test Pass Rate',v:'94 %',cls:'good',pct:94},{k:'Security Score',v:'87 / 100',cls:'good',pct:87},{k:'Failures',v:'3',cls:'bad',pct:null},{k:'Suites Run',v:'5',cls:'',pct:null}],
};

// ══════════════════════════════════════════════════════════════════════════════
//  THREE.JS SETUP
// ══════════════════════════════════════════════════════════════════════════════
const canvas = document.getElementById('c');
const W = () => window.innerWidth, H = () => window.innerHeight;

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
renderer.setSize(W(), H());
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.85;
renderer.setClearColor(0x020204, 1);

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x020204, 0.022);

const camera = new THREE.PerspectiveCamera(52, W()/H(), 0.1, 300);
camera.position.set(0, 5, 17);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.35;
controls.minDistance = 7;
controls.maxDistance = 32;

// Lighting (shared)
scene.add(new THREE.AmbientLight(0x100825, 2.5));
const keyL = new THREE.DirectionalLight(0x5b21b6, 0.5);
keyL.position.set(12,18,8);
scene.add(keyL);
const fillL = new THREE.DirectionalLight(0x0ea5e9, 0.25);
fillL.position.set(-10,5,-8);
scene.add(fillL);

// ══════════════════════════════════════════════════════════════════════════════
//  HELPERS
// ══════════════════════════════════════════════════════════════════════════════
function hex(c){ return '#'+c.toString(16).padStart(6,'0'); }
function makeParticles(n, spread, color, size=0.06){
  const g=new THREE.BufferGeometry();
  const p=new Float32Array(n*3);
  for(let i=0;i<n;i++){
    p[i*3]=(Math.random()-.5)*spread;
    p[i*3+1]=(Math.random()-.5)*spread;
    p[i*3+2]=(Math.random()-.5)*spread;
  }
  g.setAttribute('position',new THREE.BufferAttribute(p,3));
  return new THREE.Points(g, new THREE.PointsMaterial({color,size,transparent:true,opacity:.7,sizeAttenuation:true}));
}
function makeSphere(r,color,emissive=0,shininess=60){
  return new THREE.Mesh(
    new THREE.SphereGeometry(r,24,24),
    new THREE.MeshPhongMaterial({color,emissive,emissiveIntensity:.8,specular:0xffffff,shininess,transparent:true,opacity:.85})
  );
}
function makeCrystal(r,color,emissive){
  return new THREE.Mesh(
    new THREE.OctahedronGeometry(r,0),
    new THREE.MeshPhongMaterial({color,emissive,emissiveIntensity:1,specular:0xffffff,shininess:90,transparent:true,opacity:.88})
  );
}
function makeBar(color){
  return new THREE.Mesh(
    new THREE.BoxGeometry(.7,1,.7),
    new THREE.MeshPhongMaterial({color,emissive:color,emissiveIntensity:.4,transparent:true,opacity:.85})
  );
}
function makeTubeFlow(from,to,count,color){
  const offsets = Array.from({length:count},(_,k)=>k/count);
  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(count*3);
  geo.setAttribute('position',new THREE.BufferAttribute(pos,3));
  const pts = new THREE.Points(geo, new THREE.PointsMaterial({color,size:.08,transparent:true,opacity:.9,sizeAttenuation:true}));
  return {pts,pos,offsets,from:new THREE.Vector3(...from),to:new THREE.Vector3(...to),speed:.006+Math.random()*.004};
}

// ══════════════════════════════════════════════════════════════════════════════
//  OVERVIEW SCENE
// ══════════════════════════════════════════════════════════════════════════════
const ovGroup = new THREE.Group();
scene.add(ovGroup);

// Stars
{
  const g=new THREE.BufferGeometry(),n=2800,p=new Float32Array(n*3),col=new Float32Array(n*3);
  const sc=[[.4,.2,.9],[.2,.4,.9],[.6,.3,1],[.2,.6,.9],[.9,.9,1]];
  for(let i=0;i<n;i++){
    const r=80+Math.random()*140,th=Math.random()*Math.PI*2,ph=Math.acos(2*Math.random()-1);
    p[i*3]=r*Math.sin(ph)*Math.cos(th);p[i*3+1]=r*Math.sin(ph)*Math.sin(th);p[i*3+2]=r*Math.cos(ph);
    const c=sc[Math.floor(Math.random()*sc.length)];
    col[i*3]=c[0];col[i*3+1]=c[1];col[i*3+2]=c[2];
  }
  g.setAttribute('position',new THREE.BufferAttribute(p,3));
  g.setAttribute('color',new THREE.BufferAttribute(col,3));
  ovGroup.add(new THREE.Points(g,new THREE.PointsMaterial({size:.09,vertexColors:true,transparent:true,opacity:.55})));
}
{
  const g=new THREE.BufferGeometry(),n=600,p=new Float32Array(n*3);
  for(let i=0;i<n;i++){p[i*3]=(Math.random()-.5)*28;p[i*3+1]=(Math.random()-.5)*20;p[i*3+2]=(Math.random()-.5)*28;}
  g.setAttribute('position',new THREE.BufferAttribute(p,3));
  ovGroup.add(new THREE.Points(g,new THREE.PointsMaterial({color:0x4c1d95,size:.04,transparent:true,opacity:.35})));
}

// Node meshes
const nodeMeshes={};
const clickTargets=[];
NODES.forEach((n,i)=>{
  const g=new THREE.Group();
  g.position.set(...n.pos);
  g.userData={nodeId:n.id,baseY:n.pos[1],idx:i};
  const outer=new THREE.Mesh(new THREE.OctahedronGeometry(n.size*1.22,0),new THREE.MeshBasicMaterial({color:n.glow,wireframe:true,transparent:true,opacity:.12}));
  const mid=new THREE.Mesh(new THREE.OctahedronGeometry(n.size*1.08,1),new THREE.MeshBasicMaterial({color:n.glow,wireframe:true,transparent:true,opacity:.07}));
  const body=new THREE.Mesh(new THREE.OctahedronGeometry(n.size,0),new THREE.MeshPhongMaterial({color:n.color,emissive:new THREE.Color(n.emissive),emissiveIntensity:1.1,specular:new THREE.Color(n.glow),shininess:90,transparent:true,opacity:.88}));
  body.userData={nodeId:n.id};
  const core=new THREE.Mesh(new THREE.SphereGeometry(n.size*.42,12,12),new THREE.MeshBasicMaterial({color:n.glow,transparent:true,opacity:.25}));
  const ring=new THREE.Mesh(new THREE.TorusGeometry(n.size*1.0,.012,6,60),new THREE.MeshBasicMaterial({color:n.glow,transparent:true,opacity:.18}));
  ring.rotation.x=Math.PI/2+(Math.random()-.5)*.8;ring.rotation.z=Math.random()*Math.PI;
  const light=new THREE.PointLight(n.glow,.9,n.size*9);
  g.add(outer,mid,body,core,ring,light);
  ovGroup.add(g);
  nodeMeshes[n.id]={group:g,outer,body,ring,light,coreMat:core.material};
  clickTargets.push(body);
});

// Edges + flow
const ovFlows=[];
EDGES.forEach(([fi,ti])=>{
  const fn=nodeMap[fi],tn=nodeMap[ti];
  if(!fn||!tn)return;
  const fv=new THREE.Vector3(...fn.pos),tv=new THREE.Vector3(...tn.pos);
  const mid=fv.clone().lerp(tv,.5).add(new THREE.Vector3((Math.random()-.5)*1.2,(Math.random()-.5)*1.2,(Math.random()-.5)*1.2));
  const curve=new THREE.QuadraticBezierCurve3(fv,mid,tv);
  const pts=curve.getPoints(28);
  ovGroup.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),new THREE.LineBasicMaterial({color:0x1e1040,transparent:true,opacity:.45})));
  const count=5,fgeo=new THREE.BufferGeometry(),fpos=new Float32Array(count*3);
  fgeo.setAttribute('position',new THREE.BufferAttribute(fpos,3));
  const fp=new THREE.Points(fgeo,new THREE.PointsMaterial({color:fn.glow,size:.07,transparent:true,opacity:.95,sizeAttenuation:true}));
  ovGroup.add(fp);
  ovFlows.push({pts3d:fp,fpos,curve,offsets:Array.from({length:count},(_,k)=>k/count),speed:.0028+Math.random()*.002});
});

// Labels
const labelsDiv=document.getElementById('ov-labels');
const labelEls={};
NODES.forEach(n=>{
  const el=document.createElement('div');el.className='lbl';el.textContent=n.label;
  labelsDiv.appendChild(el);labelEls[n.id]=el;
});

// Health rail
const rail=document.getElementById('health-rail');
NODES.forEach(n=>{
  const el=document.createElement('div');el.className='hr-row';
  el.innerHTML=`<div class="hr-gem" style="background:${hex(n.glow)}"></div><span style="flex:1">${n.label}</span><span class="hr-ok" style="color:${hex(n.glow)}">OK</span>`;
  el.addEventListener('click',()=>enterInner(n.id));
  rail.appendChild(el);
});

// ══════════════════════════════════════════════════════════════════════════════
//  INNER SCENES
// ══════════════════════════════════════════════════════════════════════════════
const innerGroups={};
const innerAnimators={};

function buildInner(nodeId){
  const n=nodeMap[nodeId];
  const g=new THREE.Group();
  g.visible=false;
  scene.add(g);
  innerGroups[nodeId]=g;

  // Shared ambient for inner — faint star field
  const sg=new THREE.BufferGeometry(),sn=600,sp=new Float32Array(sn*3);
  for(let i=0;i<sn;i++){sp[i*3]=(Math.random()-.5)*40;sp[i*3+1]=(Math.random()-.5)*24;sp[i*3+2]=(Math.random()-.5)*40;}
  sg.setAttribute('position',new THREE.BufferAttribute(sp,3));
  g.add(new THREE.Points(sg,new THREE.PointsMaterial({color:n.glow,size:.05,transparent:true,opacity:.18})));

  // Ambient point light
  const al=new THREE.PointLight(n.glow,.6,30);g.add(al);
  const al2=new THREE.AmbientLight(n.emissive,3);g.add(al2);

  let anim;
  if(nodeId==='monitoring') anim=buildMonitoring(g,n);
  else if(nodeId==='auth')   anim=buildAuth(g,n);
  else if(nodeId==='prompt') anim=buildPrompt(g,n);
  else if(nodeId==='policy') anim=buildPolicy(g,n);
  else if(nodeId==='firewall') anim=buildFirewall(g,n);
  else if(nodeId==='models') anim=buildModels(g,n);
  else if(nodeId==='output') anim=buildOutput(g,n);
  else if(nodeId==='registry') anim=buildRegistry(g,n);
  else if(nodeId==='detection') anim=buildDetection(g,n);
  else if(nodeId==='assessment') anim=buildAssessment(g,n);
  else if(nodeId==='evaluation') anim=buildEvaluation(g,n);
  else anim=buildCore(g,n);

  innerAnimators[nodeId]=anim;
}

// MONITORING ──────────────────────────────────────────────────────────────────
function buildMonitoring(g,n){
  const bars=[],lights=[],barCols=[0x10b981,0xf59e0b,0xef4444];
  barCols.forEach((c,i)=>{
    const b=makeBar(c);b.position.set((i-1)*3,-1,0);b.scale.y=2;
    const base=new THREE.Mesh(new THREE.BoxGeometry(.75,.05,.75),new THREE.MeshBasicMaterial({color:c,transparent:true,opacity:.25}));
    base.position.set((i-1)*3,-2,0);
    const pl=new THREE.PointLight(c,1,6);pl.position.set((i-1)*3,2,0);
    g.add(b,base,pl);bars.push(b);lights.push(pl);
  });
  // Ring gauge
  const arcGeo=new THREE.TorusGeometry(2,.1,8,80,Math.PI*1.6);
  const arcMesh=new THREE.Mesh(arcGeo,new THREE.MeshBasicMaterial({color:0xef4444,transparent:true,opacity:.7}));
  arcMesh.position.set(6,0,0);arcMesh.rotation.z=-Math.PI*.8;g.add(arcMesh);
  const arcLabel=new THREE.Mesh(new THREE.SphereGeometry(.3,10,10),new THREE.MeshBasicMaterial({color:0xef4444,transparent:true,opacity:.9}));
  arcLabel.position.set(6,0,0);g.add(arcLabel);
  // Falling particles (log stream)
  const lp=makeParticles(300,18,0x22d3ee,.04);g.add(lp);
  // Ground grid
  const gg=new THREE.GridHelper(20,20,0x1e1040,0x0f0820);gg.position.y=-2;g.add(gg);

  return (t,live)=>{
    const total=live.total_requests||80;
    const blocked=live.blocked_requests||12;
    const challenged=live.challenged_requests||8;
    const allowed=Math.max(total-blocked-challenged,1);
    const maxH=5;
    [allowed,challenged,blocked].forEach((v,i)=>{
      const th=(v/total)*maxH+.2;
      bars[i].scale.y=THREE.MathUtils.lerp(bars[i].scale.y,th,.04);
      bars[i].position.y=-2+bars[i].scale.y/2;
      lights[i].position.y=bars[i].position.y+bars[i].scale.y/2+.5;
      lights[i].intensity=.6+Math.sin(t*1.5+i)*.3;
    });
    // Animate log fall
    const pa=lp.geometry.attributes.position.array;
    for(let i=0;i<300;i++){pa[i*3+1]-=.04;if(pa[i*3+1]<-12)pa[i*3+1]=12;}
    lp.geometry.attributes.position.needsUpdate=true;
    arcMesh.rotation.z+=.008;
    arcLabel.scale.setScalar(1+Math.sin(t*2)*.15);
  };
}

// AUTH ────────────────────────────────────────────────────────────────────────
function buildAuth(g,n){
  // JWT rings: header/payload/signature
  const ringColors=[0x60a5fa,0xa78bfa,0xf9a8d4];
  const rings=ringColors.map((c,i)=>{
    const r=new THREE.Mesh(new THREE.TorusGeometry(1.6+i*.8,.055+i*.02,10,90),
      new THREE.MeshPhongMaterial({color:c,emissive:c,emissiveIntensity:.4,transparent:true,opacity:.75}));
    r.rotation.x=Math.PI/2;r.position.y=(i-1)*1.4;
    const pl=new THREE.PointLight(c,.5,5);pl.position.y=(i-1)*1.4;
    g.add(r,pl);return r;
  });
  // Central key sphere
  const key=makeSphere(.55,0x60a5fa,0x1e3a8a);key.position.set(0,0,0);g.add(key);
  const keyLight=new THREE.PointLight(0x60a5fa,1.2,8);g.add(keyLight);
  // User orbit dots
  const users=[];
  for(let i=0;i<8;i++){
    const u=makeSphere(.12,0xa78bfa,0x4c1d95);
    const angle=i/8*Math.PI*2,r=3.5;
    u.userData={angle,radius:r,speed:.4+Math.random()*.3,yOff:(Math.random()-.5)*2};
    g.add(u);users.push(u);
  }
  // Connection lines from users to center
  const lineMat=new THREE.LineBasicMaterial({color:0x3730a3,transparent:true,opacity:.3});
  const connLines=users.map(u=>{
    const lg=new THREE.BufferGeometry().setFromPoints([u.position.clone(),new THREE.Vector3(0,0,0)]);
    const l=new THREE.Line(lg,lineMat);g.add(l);return l;
  });
  return (t,live)=>{
    rings[0].rotation.z=t*.45;
    rings[1].rotation.z=-t*.3;
    rings[2].rotation.z=t*.2;
    key.scale.setScalar(1+Math.sin(t*1.8)*.06);
    keyLight.intensity=1+Math.sin(t*2)*.4;
    users.forEach((u,i)=>{
      const a=u.userData.angle+t*u.userData.speed;
      u.position.set(Math.cos(a)*u.userData.radius,u.userData.yOff+Math.sin(t*.5+i)*.3,Math.sin(a)*u.userData.radius);
      const pts=connLines[i].geometry.attributes.position;
      pts.setXYZ(0,u.position.x,u.position.y,u.position.z);
      pts.needsUpdate=true;
    });
  };
}

// PROMPT GUARD ────────────────────────────────────────────────────────────────
function buildPrompt(g,n){
  // Conveyor: horizontal bars simulating text
  const textBars=[];
  for(let i=0;i<8;i++){
    const w=1+Math.random()*3;
    const b=new THREE.Mesh(new THREE.BoxGeometry(w,.12,.12),
      new THREE.MeshBasicMaterial({color:0x38bdf8,transparent:true,opacity:.35}));
    b.position.set(-4+(i%4)*2.4,(i<4?1.5:-.8)+Math.random()*.4,0);
    b.userData={baseX:-8+Math.random()*3,speed:.025+Math.random()*.02};
    g.add(b);textBars.push(b);
  }
  // Scanner beam
  const scanGeo=new THREE.PlaneGeometry(.12,6);
  const scanMat=new THREE.MeshBasicMaterial({color:0x38bdf8,transparent:true,opacity:.4,side:THREE.DoubleSide});
  const scanner=new THREE.Mesh(scanGeo,scanMat);scanner.rotation.y=Math.PI/2;g.add(scanner);
  const scanLight=new THREE.PointLight(0x38bdf8,1.5,5);g.add(scanLight);
  // Clean particles (green, pass through)
  const cleanPts=makeParticles(120,6,0x10b981,.07);g.add(cleanPts);
  // Threat particles (red, deflect)
  const threatGeo=new THREE.BufferGeometry();
  const tpos=new Float32Array(30*3);
  const tvel=[];
  for(let i=0;i<30;i++){
    tpos[i*3]=-6+Math.random()*2;tpos[i*3+1]=(Math.random()-.5)*4;tpos[i*3+2]=(Math.random()-.5)*2;
    tvel.push({vx:.04,vy:(Math.random()-.5)*.06,hit:false,x:tpos[i*3]});
  }
  threatGeo.setAttribute('position',new THREE.BufferAttribute(tpos,3));
  const threatPts=new THREE.Points(threatGeo,new THREE.PointsMaterial({color:0xef4444,size:.1,transparent:true,opacity:.9}));
  g.add(threatPts);
  return (t,live)=>{
    // Scanner sweep
    scanner.position.x=Math.sin(t*.8)*5;
    scanLight.position.copy(scanner.position);
    // Text bars scroll
    textBars.forEach(b=>{b.position.x+=b.userData.speed;if(b.position.x>6)b.position.x=-8;});
    // Clean particles drift
    const cp=cleanPts.geometry.attributes.position.array;
    for(let i=0;i<120;i++){cp[i*3]+=.015;if(cp[i*3]>8)cp[i*3]=-8;}
    cleanPts.geometry.attributes.position.needsUpdate=true;
    // Threat deflect
    const tp=threatPts.geometry.attributes.position.array;
    tvel.forEach((v,i)=>{
      if(!v.hit){tp[i*3]+=v.vx;}
      if(tp[i*3]>scanner.position.x-.3&&!v.hit){v.hit=true;v.vx=-.05;v.vy=(Math.random()-.5)*.12;}
      if(v.hit){tp[i*3]+=v.vx;tp[i*3+1]+=v.vy;}
      if(tp[i*3]<-10||tp[i*3]>10){tp[i*3]=-6+Math.random()*2;tp[i*3+1]=(Math.random()-.5)*4;v.hit=false;v.vx=.04;}
    });
    threatPts.geometry.attributes.position.needsUpdate=true;
  };
}

// POLICY ENGINE ───────────────────────────────────────────────────────────────
function buildPolicy(g,n){
  // Central decision sphere (color = risk)
  const decSphere=makeSphere(.9,0x4c1d95,0x1e0760);g.add(decSphere);
  const decLight=new THREE.PointLight(0xa78bfa,1.5,8);g.add(decLight);
  // 5 weight pillars in circle
  const weights=[.25,.20,.30,.15,.10];
  const wColors=[0x6366f1,0x8b5cf6,0xef4444,0x0ea5e9,0xf59e0b];
  const wLabels=['Model Risk','Data Sens','Prompt Risk','Rate','Trust'];
  const pillars=weights.map((w,i)=>{
    const angle=i/5*Math.PI*2,r=3.5;
    const b=makeBar(wColors[i]);
    b.position.set(Math.cos(angle)*r,-1,Math.sin(angle)*r);
    b.scale.y=w*8+.3;b.position.y=-2+b.scale.y/2;
    const pl=new THREE.PointLight(wColors[i],.5,4);pl.position.copy(b.position);pl.position.y+=b.scale.y*.5;
    // Connection line to center
    const pts=[new THREE.Vector3(b.position.x,0,b.position.z),new THREE.Vector3(0,0,0)];
    const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),
      new THREE.LineBasicMaterial({color:wColors[i],transparent:true,opacity:.2}));
    g.add(b,pl,line);return b;
  });
  // Decision zones: 3 arcs
  const zoneColors=[0x10b981,0xf59e0b,0xef4444];
  const zoneAngles=[Math.PI*.6,Math.PI*.5,Math.PI*.4];
  zoneColors.forEach((c,i)=>{
    const z=new THREE.Mesh(new THREE.TorusGeometry(5+i*.5,.04,6,60,zoneAngles[i]),
      new THREE.MeshBasicMaterial({color:c,transparent:true,opacity:.15}));
    z.rotation.x=Math.PI/2;z.rotation.z=i*Math.PI*.5;
    g.add(z);
  });
  return (t,live)=>{
    decSphere.rotation.y=t*.3;
    decSphere.rotation.x=t*.15;
    decSphere.scale.setScalar(1+Math.sin(t*1.4)*.06);
    decLight.intensity=1.2+Math.sin(t*1.8)*.5;
    pillars.forEach((p,i)=>{
      const pulse=1+Math.sin(t*.8+i)*.06;
      p.scale.x=pulse;p.scale.z=pulse;
    });
  };
}

// FIREWALL ────────────────────────────────────────────────────────────────────
function buildFirewall(g,n){
  // Vertical barrier
  const barrierGeo=new THREE.PlaneGeometry(.15,8);
  const barrierMat=new THREE.MeshBasicMaterial({color:0xef4444,transparent:true,opacity:.3,side:THREE.DoubleSide});
  const barrier=new THREE.Mesh(barrierGeo,barrierMat);
  const barrierFull=new THREE.Mesh(new THREE.PlaneGeometry(.04,8),
    new THREE.MeshBasicMaterial({color:0xf87171,transparent:true,opacity:.7,side:THREE.DoubleSide}));
  g.add(barrier,barrierFull);
  const bLight=new THREE.PointLight(0xef4444,2,10);g.add(bLight);
  // Traffic cubes
  const traffic=[];
  for(let i=0;i<18;i++){
    const isBlocked=Math.random()<.3;
    const cube=new THREE.Mesh(new THREE.BoxGeometry(.35,.35,.35),
      new THREE.MeshPhongMaterial({color:isBlocked?0xef4444:0x10b981,emissive:isBlocked?0x7f1d1d:0x064e3b,emissiveIntensity:.5,transparent:true,opacity:.85}));
    cube.position.set(-7+Math.random()*2,(Math.random()-.5)*5,(Math.random()-.5)*2);
    cube.userData={speed:.03+Math.random()*.04,blocked:isBlocked,bounced:false,vy:0};
    g.add(cube);traffic.push(cube);
  }
  // Rate meter arc
  const rateArc=new THREE.Mesh(new THREE.TorusGeometry(2,.07,8,80,Math.PI*1.4),
    new THREE.MeshBasicMaterial({color:0xf59e0b,transparent:true,opacity:.6}));
  rateArc.position.set(5,0,0);rateArc.rotation.z=-Math.PI*.7;g.add(rateArc);
  return (t,live)=>{
    bLight.intensity=1.5+Math.sin(t*3)*.8;
    barrier.material.opacity=.2+Math.sin(t*2.5)*.15;
    traffic.forEach(c=>{
      if(!c.userData.bounced){c.position.x+=c.userData.speed;}
      if(c.position.x>-0.4&&!c.userData.bounced){
        if(c.userData.blocked){c.userData.bounced=true;c.userData.speed*=-1.2;c.userData.vy=(Math.random()-.5)*.06;}
      }
      if(c.userData.bounced){c.position.x+=c.userData.speed;c.position.y+=c.userData.vy;c.userData.speed*=.98;}
      if(c.position.x>8||c.position.x<-10||Math.abs(c.position.y)>6){
        c.position.set(-7+Math.random()*2,(Math.random()-.5)*4,(Math.random()-.5)*2);
        c.userData.blocked=Math.random()<.3;c.userData.bounced=false;
        c.userData.speed=.03+Math.random()*.04;c.userData.vy=0;
        c.material.color.set(c.userData.blocked?0xef4444:0x10b981);
      }
      c.rotation.x+=.02;c.rotation.y+=.015;
    });
    rateArc.rotation.z+=.004;
  };
}

// AI MODELS ───────────────────────────────────────────────────────────────────
function buildModels(g,n){
  const modelDefs=[
    {label:'Llama-3.1',color:0x10b981,emissive:0x022c22,glow:0x34d399,pos:[-3,0,0]},
    {label:'Qwen3-1.7B',color:0x0ea5e9,emissive:0x082f49,glow:0x38bdf8,pos:[3,0,0]},
    {label:'Mistral-7B',color:0x8b5cf6,emissive:0x2e1065,glow:0xa78bfa,pos:[0,0,3.5]},
  ];
  const crystals=modelDefs.map(m=>{
    const g2=new THREE.Group();g2.position.set(...m.pos);
    const body=makeCrystal(1,m.color,m.emissive);
    const outer=new THREE.Mesh(new THREE.OctahedronGeometry(1.25,0),new THREE.MeshBasicMaterial({color:m.glow,wireframe:true,transparent:true,opacity:.12}));
    const light=new THREE.PointLight(m.glow,1.2,7);
    g2.add(body,outer,light);g.add(g2);
    return {group:g2,body,outer,pos:m.pos};
  });
  // Inference flows between models
  const flows=[];
  [[0,1],[1,2],[2,0]].forEach(([fi,ti])=>{
    const from=modelDefs[fi].pos,to=modelDefs[ti].pos;
    const count=6,geo=new THREE.BufferGeometry(),pos=new Float32Array(count*3);
    geo.setAttribute('position',new THREE.BufferAttribute(pos,3));
    const pts=new THREE.Points(geo,new THREE.PointsMaterial({color:modelDefs[fi].glow,size:.09,transparent:true,opacity:.9}));
    g.add(pts);
    flows.push({pts,pos,from:new THREE.Vector3(...from),to:new THREE.Vector3(...to),offsets:Array.from({length:count},(_,k)=>k/count),speed:.006});
  });
  // HF router central sphere
  const hub=makeSphere(.5,0x4f46e5,0x1e1b4b);hub.position.set(0,2,0);g.add(hub);
  const hubLight=new THREE.PointLight(0x818cf8,1,8);hubLight.position.set(0,2,0);g.add(hubLight);
  return (t,live)=>{
    crystals.forEach((c,i)=>{
      c.body.rotation.y=t*.3+i*1.2;c.body.rotation.x=t*.15+i*.6;
      c.outer.rotation.y=-t*.2;
      c.group.position.y=c.pos[1]+Math.sin(t*.6+i)*.2;
    });
    flows.forEach(f=>{
      f.offsets=f.offsets.map(o=>(o+f.speed)%1);
      for(let i=0;i<f.offsets.length;i++){
        const a=f.offsets[i];
        f.pos[i*3]=f.from.x+(f.to.x-f.from.x)*a;
        f.pos[i*3+1]=f.from.y+(f.to.y-f.from.y)*a+Math.sin(a*Math.PI)*.5;
        f.pos[i*3+2]=f.from.z+(f.to.z-f.from.z)*a;
      }
      f.pts.geometry.attributes.position.needsUpdate=true;
    });
    hub.rotation.y=t*.5;
    hubLight.intensity=.8+Math.sin(t*2)*.4;
  };
}

// OUTPUT GUARD ────────────────────────────────────────────────────────────────
function buildOutput(g,n){
  // Text ribbon planes
  const ribbons=[];
  for(let i=0;i<6;i++){
    const w=3+Math.random()*2;
    const r=new THREE.Mesh(new THREE.PlaneGeometry(w,.15),
      new THREE.MeshBasicMaterial({color:0xfbbf24,transparent:true,opacity:.3,side:THREE.DoubleSide}));
    r.position.set(-2,(i-2.5)*.7,(Math.random()-.5)*.5);
    r.userData={scrollX:-.04-.01*i};
    g.add(r);ribbons.push(r);
  }
  // Redaction blocks (dark boxes that appear)
  const redactBlocks=[];
  for(let i=0;i<8;i++){
    const b=new THREE.Mesh(new THREE.BoxGeometry(.6+Math.random()*.8,.18,.05),
      new THREE.MeshBasicMaterial({color:0x020204,transparent:true,opacity:0}));
    b.position.set(-3+Math.random()*6,(Math.random()-2.5)*.7,0.01);
    b.userData={delay:Math.random()*4,duration:1.5,phase:0};
    g.add(b);redactBlocks.push(b);
  }
  const scanBeam=new THREE.Mesh(new THREE.PlaneGeometry(.06,5),
    new THREE.MeshBasicMaterial({color:0xfbbf24,transparent:true,opacity:.5,side:THREE.DoubleSide}));
  g.add(scanBeam);
  const sLight=new THREE.PointLight(0xfbbf24,1.5,6);g.add(sLight);
  return (t,live)=>{
    ribbons.forEach(r=>{r.position.x+=r.userData.scrollX;if(r.position.x<-8)r.position.x=6;});
    redactBlocks.forEach(b=>{
      b.userData.phase=(t%b.userData.duration)/b.userData.duration;
      b.material.opacity=Math.sin(b.userData.phase*Math.PI)*.9;
    });
    scanBeam.position.x=Math.sin(t*.6)*5;sLight.position.copy(scanBeam.position);
  };
}

// MODEL REGISTRY ──────────────────────────────────────────────────────────────
function buildRegistry(g,n){
  const models=[
    {name:'Llama-3.1-8B',score:.78,color:0x10b981},
    {name:'Qwen3-1.7B',  score:.82,color:0x0ea5e9},
    {name:'Mistral-7B',  score:.76,color:0x8b5cf6},
    {name:'Llama-3-8B',  score:.79,color:0x6366f1},
  ];
  const cards=models.map((m,i)=>{
    const angle=i/4*Math.PI*2,r=3.2;
    const card=new THREE.Mesh(new THREE.PlaneGeometry(2.2,1.4),
      new THREE.MeshPhongMaterial({color:0x0f0a20,emissive:m.color,emissiveIntensity:.08,transparent:true,opacity:.8,side:THREE.DoubleSide}));
    card.position.set(Math.cos(angle)*r,0,Math.sin(angle)*r);
    card.rotation.y=-angle+Math.PI*.5;
    // Score bar
    const barFull=new THREE.Mesh(new THREE.BoxGeometry(1.6,.08,.02),
      new THREE.MeshBasicMaterial({color:0x1a1040,transparent:true,opacity:.5}));
    barFull.position.set(0,-.4,.01);
    const barFill=new THREE.Mesh(new THREE.BoxGeometry(m.score*1.6,.08,.02),
      new THREE.MeshBasicMaterial({color:m.color,transparent:true,opacity:.8}));
    barFill.position.set((m.score*1.6/2)-(.8),-.4,.02);
    const gl=new THREE.PointLight(m.color,.6,4);
    const cg=new THREE.Group();cg.add(card,barFull,barFill,gl);
    cg.position.set(Math.cos(angle)*r,0,Math.sin(angle)*r);
    cg.rotation.y=-angle+Math.PI*.5;
    g.add(cg);return cg;
  });
  // Posture orb in center
  const orb=makeSphere(.6,0x7c3aed,0x1e0760);g.add(orb);
  const orbLight=new THREE.PointLight(0x7c3aed,1.5,8);g.add(orbLight);
  return (t,live)=>{
    cards.forEach((c,i)=>{c.rotation.y+=.003;c.position.y=Math.sin(t*.5+i)*.3;});
    orb.rotation.y=t*.4;orbLight.intensity=1+Math.sin(t*2)*.5;
  };
}

// DETECTION ───────────────────────────────────────────────────────────────────
function buildDetection(g,n){
  // Radar disc (rotating sweep)
  const discGeo=new THREE.CircleGeometry(5,64,0,Math.PI*.5);
  const discMat=new THREE.MeshBasicMaterial({color:0xfb923c,transparent:true,opacity:.18,side:THREE.DoubleSide});
  const disc=new THREE.Mesh(discGeo,discMat);disc.rotation.x=-Math.PI/2;g.add(disc);
  // Radar outline rings
  [2,3.5,5].forEach(r=>{
    const ring=new THREE.Mesh(new THREE.TorusGeometry(r,.03,6,80),
      new THREE.MeshBasicMaterial({color:0x7c2d12,transparent:true,opacity:.3}));
    ring.rotation.x=Math.PI/2;g.add(ring);
  });
  // Threat dots (appear randomly, some get marked)
  const threats=[];
  for(let i=0;i<20;i++){
    const angle=Math.random()*Math.PI*2,r=Math.random()*4.5+.3;
    const dot=makeSphere(.12,0xef4444,0x7f1d1d);
    dot.position.set(Math.cos(angle)*r,0,Math.sin(angle)*r);
    dot.userData={angle,r,detected:false,born:Math.random()*10,visible:false};
    dot.visible=false;g.add(dot);threats.push(dot);
  }
  // Hit markers
  const hitRings=threats.map(()=>{
    const h=new THREE.Mesh(new THREE.TorusGeometry(.3,.025,6,32),
      new THREE.MeshBasicMaterial({color:0xf97316,transparent:true,opacity:0}));
    h.rotation.x=Math.PI/2;g.add(h);return h;
  });
  const scanLight=new THREE.PointLight(0xfb923c,2,6);g.add(scanLight);
  return (t,live)=>{
    disc.rotation.z=t*.8;
    const sweepAngle=t*.8%(Math.PI*2);
    scanLight.position.set(Math.cos(sweepAngle)*4,0,Math.sin(sweepAngle)*4);
    threats.forEach((dot,i)=>{
      if(t>dot.userData.born&&t<dot.userData.born+6){
        dot.visible=true;
        // Check if sweep passed over it
        const da=Math.atan2(dot.position.z,dot.position.x);
        const diff=Math.abs(((sweepAngle-da+Math.PI*3)%(Math.PI*2))-Math.PI);
        if(diff<.25){hitRings[i].position.copy(dot.position);hitRings[i].material.opacity=.8;}
        else{hitRings[i].material.opacity*=.95;}
      } else {dot.visible=false;hitRings[i].material.opacity=0;}
    });
  };
}

// ASSESSMENT ──────────────────────────────────────────────────────────────────
function buildAssessment(g,n){
  const controls=[
    {name:'LLM01 Injection',score:.9,color:0x10b981},
    {name:'LLM02 Output',   score:.85,color:0x34d399},
    {name:'LLM03 Training', score:.5,color:0xf59e0b},
    {name:'LLM04 DoS',      score:.9,color:0x10b981},
    {name:'LLM05 Supply',   score:.6,color:0xf59e0b},
    {name:'LLM06 Info',     score:.9,color:0x10b981},
    {name:'LLM07 Plugin',   score:.5,color:0x94a3b8},
    {name:'LLM08 Agency',   score:.88,color:0x10b981},
    {name:'LLM09 Reliance', score:.65,color:0xf59e0b},
    {name:'LLM10 Theft',    score:.9,color:0x10b981},
  ];
  const arcs=controls.map((c,i)=>{
    const angle=i/10*Math.PI*2,r=3.8;
    const filled=new THREE.Mesh(new THREE.TorusGeometry(.45,.08,8,40,c.score*Math.PI*2),
      new THREE.MeshPhongMaterial({color:c.color,emissive:c.color,emissiveIntensity:.4,transparent:true,opacity:.85}));
    filled.position.set(Math.cos(angle)*r,.2,Math.sin(angle)*r);
    const bg=new THREE.Mesh(new THREE.TorusGeometry(.45,.08,8,40,Math.PI*2),
      new THREE.MeshBasicMaterial({color:0x1a0a2e,transparent:true,opacity:.5}));
    bg.position.copy(filled.position);
    const pl=new THREE.PointLight(c.color,.4,2.5);pl.position.copy(filled.position);
    g.add(bg,filled,pl);return filled;
  });
  // Central posture orb
  const overallScore=controls.reduce((a,c)=>a+c.score,0)/controls.length;
  const orbColor=overallScore>.8?0x10b981:overallScore>.6?0xf59e0b:0xef4444;
  const orb=makeSphere(.8,orbColor,0x0f0a20);g.add(orb);
  const orbLight=new THREE.PointLight(orbColor,2,8);g.add(orbLight);
  return (t,live)=>{
    arcs.forEach((a,i)=>{a.rotation.y=t*.1+i*.3;a.rotation.z=t*.06;});
    orb.rotation.y=t*.4;orb.scale.setScalar(1+Math.sin(t*1.5)*.06);
    orbLight.intensity=1.5+Math.sin(t*2)*.6;
  };
}

// EVALUATION ──────────────────────────────────────────────────────────────────
function buildEvaluation(g,n){
  const suites=[
    {name:'Injection Tests', pass:8,total:8,color:0x10b981},
    {name:'PII Detection',   pass:12,total:12,color:0x34d399},
    {name:'Jailbreak Adv.',  pass:8,total:10,color:0xf59e0b},
    {name:'Auth Bypass',     pass:5,total:5,color:0x10b981},
    {name:'Latency Bench',   pass:4,total:5,color:0xf59e0b},
  ];
  const bars=suites.map((s,i)=>{
    const pct=s.pass/s.total;
    const bg=new THREE.Mesh(new THREE.BoxGeometry(3,.35,.2),
      new THREE.MeshBasicMaterial({color:0x1a0a2e,transparent:true,opacity:.5}));
    bg.position.set(0,(i-2)*1.2,0);
    const fill=new THREE.Mesh(new THREE.BoxGeometry(pct*3,.35,.2),
      new THREE.MeshPhongMaterial({color:s.color,emissive:s.color,emissiveIntensity:.4,transparent:true,opacity:.85}));
    fill.position.set((pct*3/2)-(1.5),(i-2)*1.2,.01);
    const pl=new THREE.PointLight(s.color,.5,3);pl.position.copy(fill.position);
    g.add(bg,fill,pl);return {fill,bg,pct,color:s.color};
  });
  // Pass/fail particle emitters
  const passGeo=new THREE.BufferGeometry(),passPos=new Float32Array(60*3);
  const failGeo=new THREE.BufferGeometry(),failPos=new Float32Array(20*3);
  passGeo.setAttribute('position',new THREE.BufferAttribute(passPos,3));
  failGeo.setAttribute('position',new THREE.BufferAttribute(failPos,3));
  const passPts=new THREE.Points(passGeo,new THREE.PointsMaterial({color:0x10b981,size:.1,transparent:true,opacity:.8}));
  const failPts=new THREE.Points(failGeo,new THREE.PointsMaterial({color:0xef4444,size:.1,transparent:true,opacity:.8}));
  g.add(passPts,failPts);
  const pVel=Array.from({length:60},()=>({x:(Math.random()-.5)*.04,y:.03+Math.random()*.03,life:Math.random()*5}));
  const fVel=Array.from({length:20},()=>({x:(Math.random()-.5)*.04,y:.025+Math.random()*.03,life:Math.random()*5}));
  return (t,live)=>{
    bars.forEach((b,i)=>{
      const pulse=1+Math.sin(t*.8+i)*.04;
      b.fill.scale.z=pulse;
    });
    pVel.forEach((v,i)=>{
      passPos[i*3]+=v.x;passPos[i*3+1]+=v.y;passPos[i*3+2]=0;
      v.life-=.02;if(v.life<=0){passPos[i*3]=3+Math.random()*2;passPos[i*3+1]=-3;v.life=Math.random()*5+1;}
    });
    fVel.forEach((v,i)=>{
      failPos[i*3]+=v.x;failPos[i*3+1]+=v.y;
      v.life-=.02;if(v.life<=0){failPos[i*3]=-3-Math.random()*2;failPos[i*3+1]=-3;v.life=Math.random()*4+1;}
    });
    passGeo.attributes.position.needsUpdate=true;
    failGeo.attributes.position.needsUpdate=true;
  };
}

// GATEWAY CORE ────────────────────────────────────────────────────────────────
function buildCore(g,n){
  const centralOrb=makeSphere(1.2,0x3b0fa8,0x1a0560);g.add(centralOrb);
  const centralLight=new THREE.PointLight(0x8b5cf6,2,12);g.add(centralLight);
  // 12 beams shooting out to represent each node
  const beamColors=[0x8b5cf6,0x60a5fa,0x38bdf8,0xa78bfa,0xf87171,0x34d399,0xfbbf24,0xd8b4fe,0xfb923c,0xc4b5fd,0x67e8f9,0xf9a8d4];
  const beams=beamColors.map((c,i)=>{
    const angle=i/12*Math.PI*2,pitch=(Math.random()-.5)*Math.PI*.4,r=5;
    const dir=new THREE.Vector3(Math.cos(angle)*Math.cos(pitch),Math.sin(pitch),Math.sin(angle)*Math.cos(pitch)).normalize();
    const to=dir.clone().multiplyScalar(r);
    const pts=[new THREE.Vector3(0,0,0),to];
    const line=new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),
      new THREE.LineBasicMaterial({color:c,transparent:true,opacity:.25}));
    const count=5,geo=new THREE.BufferGeometry(),pos=new Float32Array(count*3);
    geo.setAttribute('position',new THREE.BufferAttribute(pos,3));
    const flow=new THREE.Points(geo,new THREE.PointsMaterial({color:c,size:.09,transparent:true,opacity:.9}));
    const offsets=Array.from({length:count},(_,k)=>k/count);
    g.add(line,flow);
    return {flow,pos,dir,to,offsets,speed:.005+Math.random()*.005,color:c};
  });
  // Outer wireframe shell
  const shell=new THREE.Mesh(new THREE.OctahedronGeometry(2,0),
    new THREE.MeshBasicMaterial({color:0x7c3aed,wireframe:true,transparent:true,opacity:.1}));
  g.add(shell);
  return (t,live)=>{
    centralOrb.rotation.y=t*.25;centralOrb.rotation.x=t*.12;
    centralOrb.scale.setScalar(1+Math.sin(t*1.2)*.06);
    centralLight.intensity=1.8+Math.sin(t*2)*.7;
    shell.rotation.y=t*.15;shell.rotation.x=t*.07;
    beams.forEach(b=>{
      b.offsets=b.offsets.map(o=>(o+b.speed)%1);
      for(let i=0;i<b.offsets.length;i++){
        const a=b.offsets[i];
        b.pos[i*3]=b.to.x*a;b.pos[i*3+1]=b.to.y*a;b.pos[i*3+2]=b.to.z*a;
      }
      b.flow.geometry.attributes.position.needsUpdate=true;
    });
  };
}

// Build all inner scenes
NODES.forEach(n=>buildInner(n.id));

// ══════════════════════════════════════════════════════════════════════════════
//  STATE MACHINE
// ══════════════════════════════════════════════════════════════════════════════
let state='overview';  // 'overview' | 'inner'
let currentNode=null;
let liveData={total_requests:0,blocked_requests:0,allowed_requests:0,block_rate:'0',challenged_requests:0,sessions:4,clients:1,active:3,protected:4,registered:4,rules:8};
let feedInterval=null;
let feedPool=[];
let feedActive=false;

async function fetchLive(){
  const token=sessionStorage.getItem('zta_token');
  if(!token)return;
  const h={Authorization:'Bearer '+token};
  try{
    const r=await fetch('/api/v1/monitoring/metrics',{headers:h});
    if(r.ok){const d=await r.json();Object.assign(liveData,{total_requests:d.total_requests||0,blocked_requests:d.blocked_requests||0,allowed_requests:d.allowed_requests||0,block_rate:d.block_rate||'0'});}
  }catch{}
  try{
    const r2=await fetch('/api/v1/models',{headers:h});
    if(r2.ok){const d=await r2.json();const ms=d.models||d||[];liveData.active=ms.filter(m=>m.is_active).length;liveData.protected=ms.filter(m=>m.scan_status==='protected').length;liveData.registered=ms.length;}
  }catch{}
  try{
    const r3=await fetch('/api/v1/detect/rules',{headers:h});
    if(r3.ok){const d=await r3.json();const rs=d.rules||d||[];liveData.rules=rs.filter(x=>x.is_active).length;}
  }catch{}
  try{
    const r4=await fetch('/api/v1/firewall/clients',{headers:h});
    if(r4.ok){const d=await r4.json();const cs=d.clients||d||[];liveData.clients=cs.length;}
  }catch{}
  // Update topbar
  document.getElementById('tReq').textContent=liveData.total_requests;
  document.getElementById('tBlk').textContent=liveData.blocked_requests;
  const br=parseFloat(liveData.block_rate||0);
  document.getElementById('tThr').textContent=br>=40?'HIGH':br>=15?'MED':'LOW';
  document.getElementById('tMdl').textContent=liveData.active;
}

function resolveVal(v){
  if(typeof v!=='string'||!v.startsWith('live:'))return v;
  const key=v.slice(5);
  if(key==='clean_pct'){
    const total=liveData.total_requests||1;
    const pct=Math.round((1-liveData.blocked_requests/total)*100);
    return pct+'%';
  }
  return liveData[key]!==undefined?liveData[key]:v;
}

function buildMetricsHTML(nodeId){
  const defs=METRIC_DEFS[nodeId]||[];
  const n=nodeMap[nodeId];
  return defs.map(d=>{
    const val=resolveVal(d.v);
    const pct=d.pct!==null?d.pct:null;
    const barHTML=pct!==null?`<div class="mp-bar-wrap"><div class="mp-bar" style="width:${pct}%;background:${hex(n.glow)}"></div></div>`:'';
    return `<div class="mp-card"><div class="mp-key">${d.k}</div><div class="mp-val ${d.cls||''}">${val}</div>${barHTML}</div>`;
  }).join('');
}

function startFeed(nodeId){
  const list=document.getElementById('feed-list');
  feedPool=FEEDS[nodeId]||[];
  feedActive=true;
  let idx=0;
  function pushLine(){
    if(!feedActive)return;
    const [type,text]=feedPool[idx%feedPool.length];idx++;
    const div=document.createElement('div');
    div.className='fd-line new';
    const tagClass={ok:'ok',warn:'warn',bad:'bad',info:'info'}[type]||'info';
    div.innerHTML=`<span class="fd-tag ${tagClass}">[${type.toUpperCase()}]</span>${text}`;
    list.prepend(div);
    while(list.children.length>14)list.lastChild.remove();
    feedInterval=setTimeout(pushLine,600+Math.random()*1000);
  }
  pushLine();
}

function stopFeed(){
  feedActive=false;
  clearTimeout(feedInterval);
}

function enterInner(nodeId){
  if(state==='inner')return;
  state='inner';currentNode=nodeId;
  const fade=document.getElementById('fade');
  fade.classList.add('on');
  setTimeout(()=>{
    // Hide overview
    ovGroup.visible=false;
    document.getElementById('ov-back').style.display='none';
    document.getElementById('ov-top').style.display='none';
    document.getElementById('health-rail').style.display='none';
    document.getElementById('ov-legend').style.display='none';
    document.getElementById('ov-labels').style.display='none';
    // Show inner UI
    const n=nodeMap[nodeId];
    document.getElementById('inner-ui').classList.add('visible');
    const gemEl=document.getElementById('in-node-gem');
    gemEl.style.cssText=`width:10px;height:10px;transform:rotate(45deg);flex-shrink:0;background:${hex(n.glow)};box-shadow:0 0 12px ${hex(n.glow)};`;
    document.getElementById('in-node-name').textContent=n.label.toUpperCase();
    document.getElementById('in-node-sub').textContent=n.sub;
    // Metrics
    document.getElementById('mp-cards').innerHTML=buildMetricsHTML(nodeId);
    // Feed
    document.getElementById('feed-list').innerHTML='';
    startFeed(nodeId);
    // Camera for inner view
    controls.autoRotate=false;
    controls.enabled=false;
    camera.position.set(0,3,11);
    controls.target.set(0,0,0);
    // Show inner group
    innerGroups[nodeId].visible=true;
    scene.fog=new THREE.FogExp2(0x020204,.018);
    // Background color shift
    renderer.setClearColor(0x020204,1);
    fade.classList.remove('on');
  },380);
}

function exitInner(){
  if(state!=='inner')return;
  const fade=document.getElementById('fade');
  fade.classList.add('on');
  stopFeed();
  setTimeout(()=>{
    if(currentNode)innerGroups[currentNode].visible=false;
    ovGroup.visible=true;
    document.getElementById('inner-ui').classList.remove('visible');
    document.getElementById('ov-back').style.display='';
    document.getElementById('ov-top').style.display='';
    document.getElementById('health-rail').style.display='';
    document.getElementById('ov-legend').style.display='';
    document.getElementById('ov-labels').style.display='';
    // Restore camera
    controls.autoRotate=true;controls.enabled=true;
    camera.position.set(0,5,17);controls.target.set(0,0,0);
    scene.fog=new THREE.FogExp2(0x020204,.022);
    state='overview';currentNode=null;
    fade.classList.remove('on');
  },380);
}
window.exitInner=exitInner;

// ══════════════════════════════════════════════════════════════════════════════
//  RAYCASTER (overview click → enter)
// ══════════════════════════════════════════════════════════════════════════════
const raycaster=new THREE.Raycaster();
const mouse=new THREE.Vector2();
canvas.addEventListener('click',e=>{
  if(state!=='overview')return;
  mouse.x=(e.clientX/W())*2-1;
  mouse.y=-(e.clientY/H())*2+1;
  raycaster.setFromCamera(mouse,camera);
  const hits=raycaster.intersectObjects(clickTargets,false);
  if(hits.length)enterInner(hits[0].object.userData.nodeId);
});

// ══════════════════════════════════════════════════════════════════════════════
//  ANIMATION LOOP
// ══════════════════════════════════════════════════════════════════════════════
const clock=new THREE.Clock();
const tmp3=new THREE.Vector3();

function animate(){
  requestAnimationFrame(animate);
  const t=clock.getElapsedTime();

  if(state==='overview'){
    NODES.forEach((n,i)=>{
      const m=nodeMeshes[n.id];if(!m)return;
      m.group.position.y=m.group.userData.baseY+Math.sin(t*.55+i*.9)*.18;
      m.body.rotation.y=t*.28+i*.52;m.body.rotation.x=t*.14+i*.31;
      m.outer.rotation.y=-t*.18+i*.44;m.outer.rotation.z=t*.10+i*.22;
      m.outer.scale.setScalar(1+Math.sin(t*1.3+i*.7)*.05);
      m.coreMat.opacity=.18+Math.sin(t*1.8+i)*.1;
      m.ring.rotation.z=t*.08+i*.4;
      m.light.intensity=.7+Math.sin(t*1.1+i*.6)*.25;
    });
    ovFlows.forEach(f=>{
      f.offsets=f.offsets.map(o=>(o+f.speed)%1);
      for(let i=0;i<f.offsets.length;i++){
        const pt=f.curve.getPoint(f.offsets[i]);
        f.fpos[i*3]=pt.x;f.fpos[i*3+1]=pt.y;f.fpos[i*3+2]=pt.z;
      }
      f.pts3d.geometry.attributes.position.needsUpdate=true;
    });
    NODES.forEach(n=>{
      const m=nodeMeshes[n.id],el=labelEls[n.id];if(!m||!el)return;
      tmp3.set(m.group.position.x,m.group.position.y+n.size*1.55,m.group.position.z);
      tmp3.project(camera);
      if(tmp3.z>1){el.style.opacity='0';return;}
      el.style.opacity='1';
      el.style.left=((tmp3.x*.5+.5)*W())+'px';
      el.style.top=((-tmp3.y*.5+.5)*H())+'px';
    });
  }

  if(state==='inner'&&currentNode&&innerAnimators[currentNode]){
    innerAnimators[currentNode](t,liveData);
  }

  controls.update();
  renderer.render(scene,camera);
}
animate();

// ══════════════════════════════════════════════════════════════════════════════
//  RESIZE + BOOT
// ══════════════════════════════════════════════════════════════════════════════
window.addEventListener('resize',()=>{
  camera.aspect=W()/H();camera.updateProjectionMatrix();renderer.setSize(W(),H());
});
window.addEventListener('keydown',e=>{if(e.key==='Escape'&&state==='inner')exitInner();});

const ld=document.getElementById('loading');
setTimeout(()=>{ld.style.transition='opacity .6s';ld.style.opacity='0';setTimeout(()=>ld.remove(),700);},1500);

fetchLive();
setInterval(fetchLive,10000);
// Refresh metrics panel while in inner view
setInterval(()=>{
  if(state==='inner'&&currentNode){
    document.getElementById('mp-cards').innerHTML=buildMetricsHTML(currentNode);
  }
},5000);