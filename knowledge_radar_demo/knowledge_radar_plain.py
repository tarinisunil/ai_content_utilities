#!/usr/bin/env python3
"""
Knowledge Radar - single-file interactive demo for the Hidden Signals series.

Run:
    python knowledge_radar_plain.py

Then open http://127.0.0.1:8765

The six signals exposed by the demo are:
1. Connections       - what connects to what?
2. Meaning           - what is related even when words differ?
3. Communities       - what ideas gather together?
4. Movement          - what is changing over time?
5. Outliers          - what does not fit yet?
6. Emergence         - what weak signal is beginning to form a new conversation?

The final signal is intentionally phrased as emergence rather than as a claim
that the system can predict the future. The demo makes evidence visible so the
reader can inspect and correlate it.

The app uses Sentence Transformers when available. If the model package/model
is unavailable, it falls back to TF-IDF so that the demonstration still runs.
"""
from __future__ import annotations

import json
import os
import threading
import webbrowser
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

HOST = "127.0.0.1"
PORT = 8765
MODEL_NAME = os.getenv("KNOWLEDGE_RADAR_MODEL", "all-MiniLM-L6-v2")
MONTH_ORDER = ["January", "February", "March", "April"]

# The dataset is deliberately seeded so the six signals have a visible story.
DEMO_ROWS = [
    ("J01", "January", "Agents need memory to complete long-running tasks."),
    ("J02", "January", "Assistants should remember previous interactions."),
    ("J03", "January", "Persistent context helps autonomous systems continue work."),
    ("J04", "January", "Agent planning improves multi-step workflows."),
    ("J05", "January", "Tool calling lets models use external systems."),
    ("J06", "January", "Models need reliable interfaces to invoke tools."),
    ("J07", "January", "Evaluation measures whether model outputs are reliable."),
    ("J08", "January", "Benchmarking compares model performance across tasks."),
    ("J09", "January", "Synthetic data helps test AI systems."),
    ("J10", "January", "OCR extracts text from scanned documents."),
    ("J11", "January", "Document parsing turns PDFs into structured information."),
    ("J12", "January", "Information extraction identifies fields in documents."),
    ("J13", "January", "We need to trace every action an autonomous agent performs."),
    ("J14", "January", "Vector search retrieves semantically similar documents."),
    ("F01", "February", "Agent memory optimization reduces repeated context work."),
    ("F02", "February", "Conversation state lets assistants resume interrupted tasks."),
    ("F03", "February", "Planning helps an agent break a goal into steps."),
    ("F04", "February", "Multi-agent orchestration coordinates specialized agents."),
    ("F05", "February", "Tool calling enables workflows across external systems."),
    ("F06", "February", "Evaluation suites reveal regressions in model behavior."),
    ("F07", "February", "Synthetic test cases cover edge cases in evaluation."),
    ("F08", "February", "How can we inspect an agent's tool calls?"),
    ("F09", "February", "Long-running agent debugging needs execution logs."),
    ("F10", "February", "PDF extraction needs robust table parsing."),
    ("F11", "February", "Document parsing should preserve structure from reports."),
    ("F12", "February", "Information extraction can normalize invoice fields."),
    ("M01", "March", "We need logs for autonomous agent actions."),
    ("M02", "March", "Agent traces should show every tool invocation."),
    ("M03", "March", "Debugging agents requires visibility into their decisions."),
    ("M04", "March", "Execution traces make failed agent runs easier to inspect."),
    ("M05", "March", "Agent activity logs help explain unexpected behavior."),
    ("M06", "March", "Memory systems should expose context usage over time."),
    ("M07", "March", "Planning systems should explain why an agent chose a step."),
    ("M08", "March", "Agent security needs visibility into tool permissions."),
    ("M09", "March", "Benchmark reports compare model behavior under load."),
    ("M10", "March", "Synthetic evaluation catches rare tool-use failures."),
    ("M11", "March", "OCR pipelines need better handling of complex documents."),
    ("M12", "March", "Information extraction should preserve provenance."),
    ("M13", "March", "Document parsing quality depends on layout awareness."),
    ("A01", "April", "Persistent memory improves long-running agent workflows."),
    ("A02", "April", "Conversation memory can be optimized for multi-agent systems."),
    ("A03", "April", "Agent planning can search over multiple possible action sequences."),
    ("A04", "April", "Task decomposition improves multi-step agent planning."),
    ("A05", "April", "Agent security policies should constrain tool access."),
    ("A06", "April", "Permission checks should be enforced before tool execution."),
    ("A07", "April", "Trace dashboards reveal every model and tool action."),
    ("A08", "April", "Agent observability needs searchable execution traces."),
    ("A09", "April", "Monitoring agent runs helps diagnose failures quickly."),
    ("A10", "April", "Agent debugging dashboards connect decisions to outcomes."),
    ("A11", "April", "Document processing and information extraction are converging."),
    ("A12", "April", "Structured parsing improves downstream information extraction."),
    ("A13", "April", "Intelligent document workflows combine parsing and extraction."),
    ("A14", "April", "Evaluation tracks quality and reliability across the full pipeline."),
    ("A15", "April", "Benchmarks compare end-to-end document understanding."),
]

SIGNALS = [
    {
        "id": "connections",
        "n": "1",
        "name": "Connections",
        "question": "What connects to what?",
        "description": "A document can matter because it is structurally connected to many other ideas, not because it is repeated the most.",
    },
    {
        "id": "meaning",
        "n": "2",
        "name": "Meaning",
        "question": "What is related even when words differ?",
        "description": "Semantic embeddings reveal relationships that exact keyword matching misses.",
    },
    {
        "id": "communities",
        "n": "3",
        "name": "Communities",
        "question": "What ideas gather together?",
        "description": "Documents form groups around shared meaning, revealing conversations and themes.",
    },
    {
        "id": "movement",
        "n": "4",
        "name": "Movement",
        "question": "What is changing?",
        "description": "Communities can grow, shrink, split, merge, or shift position over time.",
    },
    {
        "id": "outliers",
        "n": "5",
        "name": "Outliers",
        "question": "What does not fit yet?",
        "description": "A lonely document may be noise, an opportunity, or the first hint of a new conversation.",
    },
    {
        "id": "emergence",
        "n": "6",
        "name": "Emergence",
        "question": "What weak signal is beginning to form?",
        "description": "An earlier outlier becomes more interesting when semantically related documents appear around it later.",
    },
]

HTML = r'''<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Knowledge Radar — Hidden Signals</title>
<style>
:root{--bg:#08101d;--panel:#101a2c;--panel2:#0c1525;--text:#eef4ff;--muted:#aab6cf;--line:#263655;--green:#53e4a6;--blue:#70a8ff;--orange:#ffb45f;--red:#ff7180;--cyan:#62ddff;--violet:#b99aff}
*{box-sizing:border-box} body{margin:0;background:linear-gradient(180deg,#07101b,#0d1525);color:var(--text);font:15px/1.48 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.wrap{max-width:1500px;margin:auto;padding:28px}.hero{display:flex;justify-content:space-between;gap:20px;align-items:flex-start;margin-bottom:18px}.hero h1{font-size:38px;line-height:1.05;margin:0 0 8px}.hero p{margin:0;color:var(--muted);max-width:920px}.badge{padding:8px 12px;border-radius:999px;background:#15223b;border:1px solid #304267;color:#d8e4ff;font-size:12px;white-space:nowrap}.grid{display:grid;grid-template-columns:1.35fr .75fr;gap:18px}.full{grid-column:1/-1}.panel{background:rgba(16,26,44,.96);border:1px solid var(--line);border-radius:18px;padding:16px;box-shadow:0 18px 45px rgba(0,0,0,.17)}.panel h2,.panel h3{margin:0 0 9px}.muted{color:var(--muted)}.tiny{font-size:12px;color:var(--muted)}.cards{display:grid;grid-template-columns:repeat(6,1fr);gap:9px}.card{background:#0d1728;border:1px solid var(--line);border-radius:14px;padding:11px;cursor:pointer;min-height:120px}.card:hover{border-color:#536b9a}.card.active{outline:2px solid var(--cyan);background:#14223c}.num{font-size:13px;color:var(--cyan)}.card h3{margin:5px 0 3px;font-size:16px}.card p{margin:0;color:var(--muted);font-size:12px}.question{color:#fff;font-weight:600;font-size:12px;margin:4px 0}.queryRow{display:grid;grid-template-columns:1fr auto;gap:8px}.input,textarea,select{width:100%;border:1px solid #344767;background:#091323;color:var(--text);padding:11px;border-radius:10px;outline:none}.btn{border:1px solid #3a507a;background:#162541;color:#fff;padding:10px 13px;border-radius:10px;cursor:pointer}.btn:hover{background:#203454}.notice{padding:11px 13px;border-radius:11px;background:#101e35;border:1px solid #2a3c60}.good{border-color:#2e7760;background:#0d241d}.warn{border-color:#7c5940;background:#291b12}.tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}.tab{cursor:pointer;border:1px solid var(--line);padding:8px 11px;border-radius:999px;color:var(--muted)}.tab.active{color:#fff;background:#172642;border-color:#4e6a9b}.view{display:none}.view.active{display:block}.mapWrap{position:relative;background:radial-gradient(circle at 50% 48%,#172542 0,#0f1829 46%,#0b1322 100%);border:1px solid #243454;border-radius:14px;overflow:hidden}.map{height:520px;position:relative}.axis{position:absolute;left:50%;top:0;bottom:0;border-left:1px dashed #263757;opacity:.55}.axis2{position:absolute;top:50%;left:0;right:0;border-top:1px dashed #263757;opacity:.55}.dot{position:absolute;width:14px;height:14px;border-radius:50%;transform:translate(-50%,-50%);cursor:pointer;border:2px solid rgba(255,255,255,.33);transition:.12s}.dot:hover{transform:translate(-50%,-50%) scale(1.5);box-shadow:0 0 0 7px rgba(255,255,255,.08)}.dot.selected{box-shadow:0 0 0 7px rgba(98,221,255,.15);border-color:#fff}.legend{display:flex;gap:14px;flex-wrap:wrap;margin:8px 2px}.legend span{font-size:12px;color:var(--muted)}.sw{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px}.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}.result{padding:10px;border:1px solid #263656;border-radius:12px;background:#0e1829;margin-top:7px}.score{float:right;color:#a1ebff;font-variant-numeric:tabular-nums}.pill{display:inline-block;padding:4px 7px;border-radius:999px;background:#1a2947;color:#cedaff;font-size:11px}.timeline{display:flex;gap:10px;align-items:center}.timeline input{flex:1}.month{font-size:16px;font-weight:700;min-width:80px}.bar{height:10px;background:#172541;border-radius:99px;overflow:hidden;margin-top:5px}.bar i{display:block;height:100%;background:var(--cyan)}.evidence{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.evidence .result{margin:0}.center{text-align:center}.footer{margin:18px 0;color:var(--muted);font-size:12px}.hide{display:none!important}@media(max-width:1000px){.cards{grid-template-columns:repeat(3,1fr)}.grid,.two{grid-template-columns:1fr}.evidence{grid-template-columns:1fr}.hero{display:block}.badge{display:inline-block;margin-top:10px}}@media(max-width:620px){.cards{grid-template-columns:repeat(2,1fr)}.wrap{padding:15px}.queryRow{grid-template-columns:1fr}.map{height:420px}}
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <div><h1>Knowledge Radar</h1><p>A playable experiment for the <b>Hidden Signals</b> series. Instead of reading documents one at a time, inspect six layers: connections, meaning, communities, movement, outliers, and emergence.</p></div>
    <div class="badge" id="backend">loading embedding backend…</div>
  </div>

  <section class="panel full">
    <h2>The six hidden signals</h2>
    <p class="tiny">Click any card. Each card turns one idea from the series into an observable experiment.</p>
    <div class="cards" id="signalCards"></div>
  </section>

  <div class="grid" style="margin-top:18px">
    <section class="panel">
      <h2>🧪 Playground: bring your own sentence</h2>
      <p class="muted">Rewrite an existing idea using completely different words. The wow moment is when the same semantic neighborhood still appears.</p>
      <div class="queryRow"><input class="input" id="query" value="How can an autonomous system remember what happened earlier?"/><button class="btn" onclick="runQuery()">Find hidden neighbors</button></div>
      <div id="queryResults"></div>
    </section>
    <section class="panel">
      <h2>🔎 Evidence inspector</h2>
      <div id="inspector" class="muted">Choose a signal, then click a document.</div>
      <div style="margin-top:10px"><select id="outlierSelect" onchange="inspect(this.value)"></select></div>
    </section>

    <section class="panel full">
      <div class="tabs" id="tabs">
        <div class="tab active" data-view="overview">Overview</div>
        <div class="tab" data-view="connections">1 · Connections</div>
        <div class="tab" data-view="meaning">2 · Meaning</div>
        <div class="tab" data-view="communities">3 · Communities</div>
        <div class="tab" data-view="movement">4 · Movement</div>
        <div class="tab" data-view="outliers">5 · Outliers</div>
        <div class="tab" data-view="emergence">6 · Emergence</div>
      </div>

      <div id="view-overview" class="view active">
        <h2>One map, six readings</h2>
        <p class="muted">Every dot is a document. The same map can be read in six different ways. Click a dot for evidence instead of a black-box conclusion.</p>
        <div class="mapWrap"><div class="map" id="map"><div class="axis"></div><div class="axis2"></div></div></div>
        <div class="legend"><span><i class="sw" style="background:var(--green)"></i>community member</span><span><i class="sw" style="background:var(--orange)"></i>edge candidate</span><span><i class="sw" style="background:var(--red)"></i>outlier</span><span><i class="sw" style="background:var(--cyan)"></i>selected</span></div>
      </div>

      <div id="view-connections" class="view">
        <h2>1 · Connections</h2><p class="muted">Question: <b>What connects to what?</b> This view surfaces documents with many strong semantic links and shows their nearest neighbors.</p>
        <div id="connectionView"></div>
      </div>

      <div id="view-meaning" class="view">
        <h2>2 · Meaning</h2><p class="muted">Question: <b>What is related even when words differ?</b> Type an intentionally rephrased idea above, then compare the returned neighbors.</p>
        <div class="notice good"><b>WOW TEST</b><br>Try: “How can an autonomous system remember what happened earlier?” then replace it with your own completely different wording. Do not copy the vocabulary of the dataset.</div>
        <div id="meaningView" style="margin-top:10px"></div>
      </div>

      <div id="view-communities" class="view">
        <h2>3 · Communities</h2><p class="muted">Question: <b>What ideas gather together?</b> Groups emerge from the embedding relationships rather than from labels typed into the dataset.</p>
        <div id="communityView"></div>
      </div>

      <div id="view-movement" class="view">
        <h2>4 · Movement</h2><p class="muted">Question: <b>What is changing?</b> Move through months and inspect growth, specialization, convergence and shrinking activity.</p>
        <div class="timeline"><div class="month" id="monthLabel">April</div><input id="monthSlider" type="range" min="0" max="3" value="3" oninput="renderMovement()"/></div>
        <div id="movementView" style="margin-top:10px"></div>
      </div>

      <div id="view-outliers" class="view">
        <h2>5 · Outliers</h2><p class="muted">Question: <b>What does not fit yet?</b> An outlier is not automatically valuable. It is a prompt to investigate.</p>
        <div id="outlierView"></div>
      </div>

      <div id="view-emergence" class="view">
        <h2>6 · Emergence</h2><p class="muted">Question: <b>What weak signal is beginning to form?</b> We look for earlier lonely ideas whose semantic neighborhood becomes denser in later months.</p>
        <div id="emergenceView"></div>
      </div>
    </section>

    <section class="panel full">
      <h2>🧩 Bring your own mini knowledge base</h2>
      <p class="muted">Paste one sentence per line. Use <b>Month | sentence</b> when you want the movement and emergence signals to work across time.</p>
      <textarea id="customDocs">January | Agents need memory to maintain context.
January | Assistants should remember previous interactions.
February | Tool calling lets models use external systems.
March | How do we know what an autonomous agent actually did?
April | Agent traces should show every tool invocation.
April | Evaluation measures model quality.</textarea>
      <button class="btn" style="margin-top:10px" onclick="loadCustom()">Load my documents into the radar</button>
      <div id="customMsg" class="tiny" style="margin-top:8px"></div>
    </section>
  </div>
  <div class="footer">This experiment does not claim to predict the future. It exposes evidence: similarity scores, connection counts, communities, change over time, outliers, and emerging neighborhoods.</div>
</div>
<script>
let DATA=null, selectedId=null, activeView='overview';
const colors=['#53e4a6','#70a8ff','#62ddff','#ffb45f','#b99aff','#ff7180','#76e08b','#f8cf68','#8bd3dd'];
const esc=s=>String(s).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
async function getJSON(url,opts){const r=await fetch(url,opts); if(!r.ok) throw new Error(await r.text()); return r.json();}
function renderSignals(){document.getElementById('signalCards').innerHTML=DATA.signals.map(s=>`<div class="card ${s.id===activeView?'active':''}" onclick="activate('${s.id}')"><div class="num">SIGNAL ${s.n}</div><h3>${esc(s.name)}</h3><div class="question">${esc(s.question)}</div><p>${esc(s.description)}</p></div>`).join('');}
function activate(id){const map={connections:'connections',meaning:'meaning',communities:'communities',movement:'movement',outliers:'outliers',emergence:'emergence'}; const v=map[id]||'overview'; if(id==='connections'||id==='meaning'||id==='communities'||id==='movement'||id==='outliers'||id==='emergence') activeView=id; renderSignals(); showView(v);}
function showView(v){activeView=v; document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t.dataset.view===v));document.querySelectorAll('.view').forEach(x=>x.classList.toggle('active',x.id==='view-'+v)); if(v==='connections')renderConnections();if(v==='communities')renderCommunities();if(v==='movement')renderMovement();if(v==='outliers')renderOutliers();if(v==='emergence')renderEmergence();}
document.getElementById('tabs').addEventListener('click',e=>{const t=e.target.closest('.tab');if(t)showView(t.dataset.view);});
function renderMap(){const map=document.getElementById('map');map.querySelectorAll('.dot').forEach(x=>x.remove());const xs=DATA.documents.map(d=>d.x),ys=DATA.documents.map(d=>d.y);const xmin=Math.min(...xs),xmax=Math.max(...xs),ymin=Math.min(...ys),ymax=Math.max(...ys);DATA.documents.forEach(d=>{let px=8+84*((d.x-xmin)/(xmax-xmin||1)),py=8+84*((d.y-ymin)/(ymax-ymin||1));const dot=document.createElement('div');dot.className='dot'+(d.id===selectedId?' selected':'');dot.style.left=px+'%';dot.style.top=(92-py)+'%';dot.style.background=d.outlier_score>=0.78?'#ff7180':d.outlier_score>=0.58?'#ffb45f':colors[(d.cluster<0?0:d.cluster)%colors.length];dot.title=d.text;dot.onclick=()=>inspect(d.id);map.appendChild(dot);});}
function inspect(id){selectedId=id;const d=DATA.documents.find(x=>x.id===id);if(!d)return;renderMap();const neighbors=DATA.neighbors[id]||[];const chain=DATA.emergence.find(x=>x.id===id);let html=`<div class="pill">${esc(d.month)} · ${esc(d.id)}</div><h3 style="margin:7px 0">${esc(d.text)}</h3><div class="evidence"><div class="result"><div class="tiny">connections</div><strong>${d.connection_count}</strong></div><div class="result"><div class="tiny">outlier score</div><strong>${d.outlier_score.toFixed(3)}</strong></div><div class="result"><div class="tiny">community</div><strong>${d.cluster<0?'edge':d.cluster}</strong></div></div>`;
html+=`<div class="signal" style="margin-top:10px"><b>Signal reading</b><br>${esc(d.signal.title)}<br><span class="muted">${esc(d.signal.explanation)}</span></div>`;
if(neighbors.length){html+='<div style="margin-top:10px"><b>Nearest semantic neighbors</b>'+neighbors.map(n=>`<div class="result"><span class="score">${n.similarity.toFixed(3)}</span><strong>${esc(n.text)}</strong><div class="tiny">${esc(n.month)}</div></div>`).join('')+'</div>'}
if(chain){html+=`<div class="notice ${chain.emergence_score>=0.6?'good':'warn'}" style="margin-top:10px"><b>Emergence evidence</b><br>${esc(chain.message)}</div>`}
document.getElementById('inspector').innerHTML=html;}
function populateOutliers(){const s=document.getElementById('outlierSelect');s.innerHTML=DATA.outliers.slice(0,12).map(d=>`<option value="${esc(d.id)}">${esc(d.month)} — ${esc(d.text.slice(0,75))}</option>`).join('');if(DATA.outliers[0])inspect(DATA.outliers[0].id);}
function runQuery(){const q=document.getElementById('query').value.trim();if(!q)return;getJSON('/api/query?q='+encodeURIComponent(q)).then(r=>{let html=`<div class="notice ${r.top_score>=0.65?'good':'warn'}" style="margin-top:10px"><b>Meaning signal:</b> ${esc(r.message)}</div><div class="results">`;html+=r.results.map(x=>`<div class="result"><span class="score">${x.similarity.toFixed(3)}</span><strong>${esc(x.text)}</strong><div class="tiny">${esc(x.month)}</div></div>`).join('');html+='</div>';document.getElementById('queryResults').innerHTML=html;document.getElementById('meaningView').innerHTML=html;showView('meaning');});}
function renderConnections(){const top=[...DATA.documents].sort((a,b)=>b.connection_count-a.connection_count).slice(0,10);document.getElementById('connectionView').innerHTML=top.map(d=>`<div class="result" style="cursor:pointer" onclick="inspect('${d.id}')"><span class="score">${d.connection_count} links</span><strong>${esc(d.text)}</strong><div class="tiny">average neighbor strength ${d.avg_neighbor_similarity.toFixed(3)} · ${esc(d.month)}</div></div>`).join('');}
function renderCommunities(){const groups={};DATA.documents.forEach(d=>{const k=d.cluster<0?'edge / unassigned':String(d.cluster);(groups[k]??=[]).push(d)});let html='<div class="evidence">';Object.entries(groups).sort((a,b)=>b[1].length-a[1].length).forEach(([k,ds])=>{html+=`<div class="result"><div class="tiny">community ${esc(k)}</div><strong>${ds.length} documents</strong><div class="tiny" style="margin-top:6px">${ds.slice(0,3).map(d=>esc(d.text)).join(' · ')}</div></div>`});html+='</div>';document.getElementById('communityView').innerHTML=html;}
function renderMovement(){const months=DATA.months,idx=Number(document.getElementById('monthSlider').value),month=months[idx],prev=months[idx-1];document.getElementById('monthLabel').textContent=month;const current=DATA.movement[month]||{};const prior=prev?(DATA.movement[prev]||{}):{};let growth=Object.keys(current).map(k=>({k,delta:(current[k]?.size||0)-(prior[k]?.size||0),size:current[k]?.size||0})).sort((a,b)=>b.delta-a.delta).slice(0,6);let html=`<div class="notice good"><b>Movement signal:</b> the shape of the collection matters more than the raw document count. Compare which communities gain or lose members.</div><div class="evidence" style="margin-top:10px">${growth.map(g=>`<div class="result"><div class="tiny">community ${esc(g.k)}</div><strong>${g.delta>0?'+':''}${g.delta} documents</strong><div class="tiny">size now ${g.size}</div></div>`).join('')}</div>`;if(idx>0){const splits=DATA.movementEvents.filter(e=>e.kind==='split'&&e.month===month);const merges=DATA.movementEvents.filter(e=>e.kind==='merge'&&e.month===month);if(splits.length||merges.length)html+=`<div style="margin-top:10px" class="notice"><b>Structural events:</b> ${splits.map(e=>esc(e.message)).concat(merges.map(e=>esc(e.message))).join(' · ')}</div>`;}document.getElementById('movementView').innerHTML=html;}
function renderOutliers(){document.getElementById('outlierView').innerHTML=DATA.outliers.slice(0,10).map(d=>`<div class="result" style="cursor:pointer" onclick="inspect('${d.id}')"><span class="score">${d.outlier_score.toFixed(3)}</span><strong>${esc(d.text)}</strong><div class="tiny">${esc(d.month)} · ${esc(d.signal.title)}</div></div>`).join('');}
function renderEmergence(){let arr=[...DATA.emergence].sort((a,b)=>b.emergence_score-a.emergence_score).slice(0,10);document.getElementById('emergenceView').innerHTML='<div class="notice good"><b>Emergence signal:</b> earlier weakly-connected ideas become more interesting when related documents appear around them later.</div>'+arr.map(e=>`<div class="result" style="cursor:pointer" onclick="inspect('${e.id}')"><span class="score">${e.emergence_score.toFixed(3)}</span><strong>${esc(e.text)}</strong><div class="tiny">started ${esc(e.month)} · later related docs ${e.later_neighbor_count} · ${esc(e.message)}</div></div>`).join('');}
async function loadCustom(){const lines=document.getElementById('customDocs').value.split(/\n+/).map(x=>x.trim()).filter(Boolean);const docs=lines.map((x,i)=>{const p=x.split('|',2);return{id:'U'+String(i+1).padStart(3,'0'),month:p.length===2?p[0].trim():'Now',text:(p.length===2?p[1]:p[0]).trim()}});try{DATA=await getJSON('/api/custom',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(docs)});selectedId=null;renderAll();document.getElementById('customMsg').textContent=`Loaded ${docs.length} documents. Try a radically rephrased sentence above, then inspect the other five signals.`;}catch(e){document.getElementById('customMsg').textContent=e.message;}}
function renderAll(){document.getElementById('backend').textContent=DATA.backend;renderSignals();renderMap();populateOutliers();renderConnections();renderCommunities();renderMovement();renderOutliers();renderEmergence();runQuery();}
async function load(){DATA=await getJSON('/api/data');renderAll();}
load();
</script>
</body>
</html>'''


def normalize_rows(rows):
    return pd.DataFrame(rows, columns=["id", "month", "text"])


def outlier_scores(sim):
    vals=[]
    for i in range(len(sim)):
        row=np.delete(sim[i],i)
        if len(row)==0:
            vals.append(1.0);continue
        k=min(5,len(row))
        vals.append(1.0-float(np.mean(np.sort(row)[-k:])))
    return np.asarray(vals)


class RadarEngine:
    def __init__(self,df):
        self.set_data(df)

    def set_data(self,df):
        self.df=df.reset_index(drop=True).copy()
        self.backend_name="TF-IDF fallback"
        self.backend_note="Lexical similarity; install sentence-transformers for semantic embeddings."
        self.model=None
        self.vectorizer=None
        if SentenceTransformer is not None:
            try:
                self.model=SentenceTransformer(MODEL_NAME)
                self.emb=np.asarray(self.model.encode(self.df.text.tolist(),normalize_embeddings=True,show_progress_bar=False))
                self.backend_name=f"Sentence Transformers · {MODEL_NAME}"
                self.backend_note="Semantic embeddings"
            except Exception:
                self.model=None
        if self.model is None:
            self.vectorizer=TfidfVectorizer(stop_words="english",ngram_range=(1,2),min_df=1)
            self.emb=self.vectorizer.fit_transform(self.df.text).toarray()
        self.sim=cosine_similarity(self.emb)
        self.out=outlier_scores(self.sim)
        self.labels=DBSCAN(eps=0.42,min_samples=2,metric="cosine").fit_predict(self.emb) if len(self.df)>=2 else np.zeros(len(self.df),dtype=int)
        if len(self.emb)>=2:
            self.xy=PCA(n_components=2,random_state=42).fit_transform(self.emb)
        else:
            self.xy=np.zeros((1,2))
        self._build_metrics()

    def _build_metrics(self):
        self.df["month_idx"]=self.df.month.map({m:i for i,m in enumerate(self.months())}).fillna(-1).astype(int)
        threshold=0.62 if self.model is not None else 0.18
        self.connection_counts=[];self.avg_neighbor=[]
        for i in range(len(self.df)):
            vals=np.delete(self.sim[i],i)
            links=int(np.sum(vals>=threshold))
            self.connection_counts.append(links)
            self.avg_neighbor.append(float(np.mean(np.sort(vals)[-min(5,len(vals)):])) if len(vals) else 0.0)
        self.connection_counts=np.asarray(self.connection_counts);self.avg_neighbor=np.asarray(self.avg_neighbor)
        self.movement=self._movement_summary()
        self.movementEvents=self._movement_events()
        self.emergence=self._emergence()

    def months(self):
        vals=self.df.month.drop_duplicates().tolist()
        preferred=[m for m in MONTH_ORDER if m in vals]
        return preferred+[m for m in vals if m not in preferred]

    def _movement_summary(self):
        result={}
        months=self.months()
        for m in months:
            sub=self.df[self.df.month==m]
            by=defaultdict(list)
            for idx in sub.index:
                by[int(self.labels[idx])].append(idx)
            result[m]={str(k):{"size":len(v),"ids":[str(self.df.iloc[i].id) for i in v]} for k,v in by.items()}
        return result

    def _movement_events(self):
        events=[]
        months=self.months()
        for i in range(1,len(months)):
            prev,curr=months[i-1],months[i]
            p=self.movement.get(prev,{})
            c=self.movement.get(curr,{})
            ps=sorted([(k,v["size"]) for k,v in p.items() if k!="-1"],key=lambda x:-x[1])
            cs=sorted([(k,v["size"]) for k,v in c.items() if k!="-1"],key=lambda x:-x[1])
            if ps and cs:
                ptop=ps[0][0]; ctop=cs[0][0]
                if cs[0][1]>=ps[0][1]+2:
                    events.append({"month":curr,"kind":"growth","message":f"Community {ctop} grew materially from {ps[0][1]} to {cs[0][1]} documents."})
            # Heuristic split: one prior community maps to multiple current groups by semantic centroid overlap.
            for pk,pdata in p.items():
                if pk=="-1" or pdata["size"]<4: continue
                overlaps=[]
                pidx=[self.df.index[self.df.id==x][0] for x in pdata["ids"] if len(self.df.index[self.df.id==x])]
                pcent=np.mean(self.emb[pidx],axis=0)
                for ck,cdata in c.items():
                    if ck=="-1": continue
                    cidx=[self.df.index[self.df.id==x][0] for x in cdata["ids"] if len(self.df.index[self.df.id==x])]
                    if not cidx: continue
                    sim=float(cosine_similarity([pcent],[np.mean(self.emb[cidx],axis=0)])[0,0])
                    if sim>0.55: overlaps.append(ck)
                if len(overlaps)>=2:
                    events.append({"month":curr,"kind":"split","message":f"Community {pk} may be specializing into communities {', '.join(overlaps[:3])}."})
        return events

    def _emergence(self):
        months=self.months(); result=[]
        for i,row in self.df.iterrows():
            later=[]
            for j,r2 in self.df.iterrows():
                if i==j: continue
                if self.df.loc[j,"month_idx"]>self.df.loc[i,"month_idx"] and self.sim[i,j] >= (0.58 if self.model is not None else 0.10):
                    later.append(j)
            early_out=self.out[i]
            later_count=len(later)
            later_strength=float(np.mean([self.sim[i,j] for j in later])) if later else 0.0
            # Emphasis on "lonely first, then neighborhood" rather than a black-box forecast.
            score=min(1.0,0.55*early_out+0.30*min(1,later_count/5)+0.15*later_strength)
            if early_out<0.45 and later_count<2: score*=0.35
            msg=(f"{later_count} later related documents appear around this earlier idea."
                 if later_count else "No meaningful later neighborhood detected yet.")
            result.append({"id":str(row.id),"month":str(row.month),"text":str(row.text),"later_neighbor_count":later_count,"emergence_score":float(score),"message":msg})
        return result

    def encode_query(self,text):
        if self.model is not None:
            return np.asarray(self.model.encode([text],normalize_embeddings=True,show_progress_bar=False))
        return self.vectorizer.transform([text]).toarray()

    def query(self,text,top_k=8):
        q=self.encode_query(text)
        scores=cosine_similarity(q,self.emb)[0]
        idx=np.argsort(scores)[::-1][:min(top_k,len(scores))]
        top=float(scores[idx[0]]) if len(idx) else 0.0
        threshold=0.65 if self.model is not None else 0.20
        if top>=threshold:
            msg="Your wording landed near an existing semantic neighborhood. The vocabulary changed, but the relationship remained visible."
        else:
            msg="No strong neighborhood appeared. Try another paraphrase or add more documents to your knowledge base."
        return {"top_score":top,"message":msg,"results":[{"id":str(self.df.iloc[i].id),"similarity":float(scores[i]),"month":str(self.df.iloc[i].month),"text":str(self.df.iloc[i].text)} for i in idx]}

    def signal_for(self,i):
        score=float(self.out[i])
        conn=int(self.connection_counts[i])
        if score>=0.78:
            return {"title":"Outlier: weak local neighborhood","explanation":"This document is relatively isolated. That can be noise, a one-off note, or an early idea. The useful test is what happens later."}
        if conn>=6:
            return {"title":"Connection hub: many nearby ideas","explanation":"This document has many strong semantic links. Its structural position is more informative than simply counting repeated words."}
        if score>=0.58:
            return {"title":"Edge document: worth watching","explanation":"This document sits toward the edge of the existing communities. Watch whether related ideas gather around it."}
        return {"title":"Community member: established conversation","explanation":"This document has several nearby ideas, so it looks like part of an existing conversation rather than an isolated edge signal."}

    def payload(self):
        months=self.months();x=self.xy[:,0];y=self.xy[:,1];xn=(x-x.min())/(x.max()-x.min()+1e-9);yn=(y-y.min())/(y.max()-y.min()+1e-9)
        docs=[]
        for i,row in self.df.iterrows():
            docs.append({"id":str(row.id),"month":str(row.month),"text":str(row.text),"x":float(xn[i]),"y":float(yn[i]),"cluster":int(self.labels[i]),"outlier_score":float(self.out[i]),"connection_count":int(self.connection_counts[i]),"avg_neighbor_similarity":float(self.avg_neighbor[i]),"signal":self.signal_for(i)})
        out_idx=np.argsort(self.out)[::-1][:min(12,len(self.df))]
        outs=[docs[i] for i in out_idx]
        neighbors={}
        for i in range(len(self.df)):
            order=np.argsort(self.sim[i])[::-1];order=[j for j in order if j!=i][:7]
            neighbors[str(self.df.iloc[i].id)]=[{"month":str(self.df.iloc[j].month),"text":str(self.df.iloc[j].text),"similarity":float(self.sim[i,j])} for j in order]
        return {"backend":f"{self.backend_name} — {self.backend_note}","signals":SIGNALS,"months":months,"documents":docs,"outliers":outs,"neighbors":neighbors,"movement":self.movement,"movementEvents":self.movementEvents,"emergence":self.emergence}

ENGINE=RadarEngine(normalize_rows(DEMO_ROWS))

class Handler(BaseHTTPRequestHandler):
    def _send(self,body,status=200,content_type="application/json; charset=utf-8"):
        if isinstance(body,str): body=body.encode("utf-8")
        self.send_response(status);self.send_header("Content-Type",content_type);self.send_header("Content-Length",str(len(body)));self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(body)
    def do_GET(self):
        p=urlparse(self.path)
        if p.path=="/": self._send(HTML,content_type="text/html; charset=utf-8");return
        if p.path=="/api/data": self._send(json.dumps(ENGINE.payload()).encode());return
        if p.path=="/api/query":
            q=parse_qs(p.query).get("q",[""])[0]
            if not q.strip(): self._send(json.dumps({"error":"empty query"}),400);return
            self._send(json.dumps(ENGINE.query(q)).encode());return
        self._send(json.dumps({"error":"not found"}),404)
    def do_POST(self):
        global ENGINE
        if urlparse(self.path).path!="/api/custom": self._send(json.dumps({"error":"not found"}),404);return
        length=int(self.headers.get("Content-Length","0"));raw=self.rfile.read(length)
        try:
            docs=json.loads(raw.decode("utf-8"));df=pd.DataFrame(docs)
            if df.empty or not {"id","month","text"}.issubset(df.columns): raise ValueError("Expected id/month/text")
            if len(df)>250: raise ValueError("Keep the demo under 250 documents")
            ENGINE=RadarEngine(df[["id","month","text"]].astype(str));self._send(json.dumps(ENGINE.payload()).encode())
        except Exception as e: self._send(json.dumps({"error":str(e)}),400)
    def log_message(self,format,*args): return

def main():
    server=ThreadingHTTPServer((HOST,PORT),Handler);url=f"http://{HOST}:{PORT}"
    print(f"Knowledge Radar running at {url}")
    print(f"Embedding backend: {ENGINE.backend_name}")
    if ENGINE.model is None: print("Semantic backend unavailable: using TF-IDF fallback; install requirements.txt for embeddings.")
    print("Press Ctrl+C to stop.")
    threading.Timer(0.6,lambda:webbrowser.open(url)).start()
    try: server.serve_forever()
    except KeyboardInterrupt: print("\nStopping Knowledge Radar");server.server_close()

if __name__=="__main__": main()
