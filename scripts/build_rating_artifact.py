"""Build a self-contained rating dashboard for publishing as an Artifact.

Artifacts run under a strict CSP with no external requests, so the store is
inlined rather than fetched. The raw scraper payload is dropped first — it
duplicates every field and would triple the file for no benefit.

The point of this build is not to display the pipeline. It is to make rating
fast: criteria for the domain you are looking at are on screen, keyboard keys
1-5 set a band, and the export produces exactly the CSV merge_review.py wants.

Usage:
    python scripts/build_rating_artifact.py
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_labelling_guide import BANDS, GUIDE, UNIVERSAL  # noqa: E402

STORE = ROOT / "docs" / "design_previews" / "2026-07-28-live" / "intelligence_store.json"
OUT = ROOT / "docs" / "design_previews" / "2026-07-28-live" / "rating_dashboard.html"


def compact(store: dict) -> dict:
    """Strip everything the rating UI does not use."""
    out = []
    for s in store["signals"]:
        d = (s["domains"] or [{}])[0]
        ents = s.get("entities") or {}
        out.append({
            "t": s["title"],
            "u": s["canonical_url"],
            "p": s["publisher"],
            "d": s.get("engine_id") or "",
            "dn": d.get("display", ""),
            "b": s["priority"],
            "sc": s["impact"]["score"],
            "dim": s["impact"]["dimensions"],
            "ev": [e["keyword"] for e in d.get("evidence", [])],
            "evt": [e["type"] for e in s.get("events", [])],
            "age": (s.get("freshness") or {}).get("age_hours"),
            "fb": (s.get("freshness") or {}).get("bucket", ""),
            "tier": s["source"]["tier"],
            "ent": [e["value"] for k in ("companies", "regulators", "countries")
                    for e in (ents.get(k) or [])][:3],
            "why": [{"s": e["stage"], "r": e["reason"]} for e in s.get("explain", [])],
        })
    out.sort(key=lambda r: -r["sc"])
    return {"data_date": store["data_date"], "counts": store["counts"], "rows": out}


def guide_payload() -> dict:
    return {dom: {"display": spec["display"],
                  "bands": {b: {"q": spec[b][0], "test": spec[b][1], "miss": spec[b][2]}
                            for b in BANDS}}
            for dom, spec in GUIDE.items()}


HTML = """<title>SIGNAL — Rate Today's Intelligence</title>
<style>
:root{
  --ground:#ffffff; --raised:#f7f8fa; --sunk:#eef1f5;
  --ink:#0f1620; --ink-2:#48525f; --ink-3:#7c8794;
  --rule:#e0e5eb; --rule-soft:#eef1f5;
  --navy:#0b1524; --accent:#2f6fed; --accent-soft:#eaf0fe;
  --sev-must:#e11d2e; --sev-imp:#b45309; --sev-watch:#2f6fed; --sev-bg:#94a3b1;
  --good:#0e7c5a; --good-soft:#eefaf4;
  --serif:Georgia,"Times New Roman",serif;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,sans-serif;
  --mono:"SF Mono",Consolas,"Liberation Mono",monospace;
}
@media (prefers-color-scheme:dark){
  :root{ --ground:#0c1219; --raised:#131b24; --sunk:#0a0f15;
    --ink:#e9edf2; --ink-2:#a3aeba; --ink-3:#6c7885;
    --rule:#1f2a36; --rule-soft:#161f29; --navy:#060b12;
    --accent:#6c9bff; --accent-soft:#16233a;
    --sev-must:#ff5f6d; --sev-imp:#d68a3a; --sev-watch:#6c9bff; --sev-bg:#5a6674;
    --good:#3ec695; --good-soft:#0f2620; }
}
:root[data-theme="dark"]{ --ground:#0c1219; --raised:#131b24; --sunk:#0a0f15;
  --ink:#e9edf2; --ink-2:#a3aeba; --ink-3:#6c7885;
  --rule:#1f2a36; --rule-soft:#161f29; --navy:#060b12;
  --accent:#6c9bff; --accent-soft:#16233a;
  --sev-must:#ff5f6d; --sev-imp:#d68a3a; --sev-watch:#6c9bff; --sev-bg:#5a6674;
  --good:#3ec695; --good-soft:#0f2620; }
:root[data-theme="light"]{ --ground:#ffffff; --raised:#f7f8fa; --sunk:#eef1f5;
  --ink:#0f1620; --ink-2:#48525f; --ink-3:#7c8794;
  --rule:#e0e5eb; --rule-soft:#eef1f5; --navy:#0b1524;
  --accent:#2f6fed; --accent-soft:#eaf0fe;
  --sev-must:#e11d2e; --sev-imp:#b45309; --sev-watch:#2f6fed; --sev-bg:#94a3b1;
  --good:#0e7c5a; --good-soft:#eefaf4; }

*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);
     font-size:15px;line-height:1.5;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
.wrap{max-width:1120px;margin:0 auto;padding:0 24px}
.tnum{font-variant-numeric:tabular-nums}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}

/* masthead */
header{background:var(--navy);color:#fff;padding:16px 0;border-bottom:3px solid var(--sev-must)}
header .wrap{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.mark{width:26px;height:26px;flex:none}
.word{font-weight:800;letter-spacing:.22em;font-size:15px}
.sub{font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;
     color:rgba(255,255,255,.55)}
header .asof{margin-left:auto;font-family:var(--mono);font-size:10px;letter-spacing:.08em;
             color:rgba(255,255,255,.6)}
header .asof b{color:#fff}

/* control bar */
.bar{position:sticky;top:0;z-index:20;background:var(--raised);border-bottom:1px solid var(--rule);
     padding:11px 0}
.bar .wrap{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.prog{flex:1;min-width:180px;display:flex;align-items:center;gap:10px}
.prog .track{flex:1;height:6px;background:var(--sunk);border-radius:3px;overflow:hidden}
.prog .fill{height:100%;background:var(--accent);width:0;transition:width .25s ease}
.prog .n{font-family:var(--mono);font-size:11px;color:var(--ink-2);white-space:nowrap}
select,.btn{font-family:var(--mono);font-size:11px;padding:6px 11px;border:1px solid var(--rule);
  background:var(--ground);color:var(--ink);border-radius:4px;cursor:pointer}
.btn:hover,select:hover{border-color:var(--accent);color:var(--accent)}
.btn.primary{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:700}
.btn.primary:hover{opacity:.9;color:#fff}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

/* criteria panel */
.crit{background:var(--sunk);border-bottom:1px solid var(--rule);padding:16px 0;display:none}
.crit.open{display:block}
.crit h3{font-family:var(--mono);font-size:10px;letter-spacing:.16em;text-transform:uppercase;
         color:var(--ink-3);margin:0 0 10px}
.crit-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(196px,1fr));gap:12px}
.crit-cell{background:var(--ground);border:1px solid var(--rule);border-radius:5px;padding:11px 12px;
           border-top:3px solid var(--band)}
.crit-cell .b{font-family:var(--mono);font-size:10px;letter-spacing:.1em;font-weight:700;
              color:var(--band);margin-bottom:6px}
.crit-cell .q{font-size:12.5px;line-height:1.45;color:var(--ink)}
.crit-cell .t{font-size:11.5px;line-height:1.45;color:var(--ink-2);margin-top:7px;font-style:italic}

/* rows */
.band-h{display:flex;align-items:baseline;gap:10px;padding:26px 0 9px;
        border-bottom:2px solid var(--band);margin-bottom:2px}
.band-h h2{font-family:var(--mono);font-size:11.5px;letter-spacing:.2em;text-transform:uppercase;
           color:var(--band);margin:0}
.band-h .c{font-family:var(--mono);font-size:10.5px;color:var(--ink-3);margin-left:auto}

.row{display:grid;grid-template-columns:4px 46px 1fr 128px;gap:14px;padding:14px 0;
     border-bottom:1px solid var(--rule-soft);align-items:start}
.row .stripe{background:var(--band);border-radius:2px;align-self:stretch;min-height:38px}
.row.rated{background:var(--accent-soft)}
.sc{font-family:var(--mono);text-align:right;padding-top:2px}
.sc .v{font-size:15px;font-weight:700}
.sc .l{font-size:9px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3);display:block;margin-top:2px}
.kick{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:5px}
.pub{font-size:11.5px;font-weight:700;color:var(--ink)}
.dom{font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--accent)}
h4{font-family:var(--serif);font-weight:400;font-size:17.5px;line-height:1.34;margin:0;
   text-wrap:balance;color:var(--ink)}
h4 a:hover{color:var(--accent);text-decoration:underline}
.chips{display:flex;gap:5px;flex-wrap:wrap;margin-top:8px}
.chip{font-family:var(--mono);font-size:8.5px;letter-spacing:.05em;text-transform:uppercase;
      padding:2px 6px;border-radius:3px;border:1px solid var(--rule);color:var(--ink-3)}
.chip.evt{border-color:var(--sev-imp);color:var(--sev-imp)}
.chip.t1{border-color:var(--good);color:var(--good);background:var(--good-soft)}
details{margin-top:8px}
summary{font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;
        color:var(--ink-3);cursor:pointer}
summary:hover{color:var(--accent)}
.trace{margin-top:7px;border-left:2px solid var(--rule);padding-left:11px;
       display:grid;grid-template-columns:70px 1fr;gap:3px 10px;font-size:12px}
.trace .s{font-family:var(--mono);font-size:9px;text-transform:uppercase;color:var(--accent);padding-top:2px}
.trace .r{color:var(--ink-2);line-height:1.4}

.rate{display:flex;flex-direction:column;gap:3px}
.rate .lbl{font-family:var(--mono);font-size:8.5px;letter-spacing:.1em;text-transform:uppercase;
           color:var(--ink-3);margin-bottom:2px}
.rate button{font-family:var(--mono);font-size:9.5px;letter-spacing:.04em;padding:5px 7px;
  border:1px solid var(--rule);background:var(--ground);color:var(--ink-2);border-radius:3px;
  cursor:pointer;text-align:left;display:flex;gap:6px;align-items:center}
.rate button:hover{border-color:var(--accent);color:var(--accent)}
.rate button.on{background:var(--navy);border-color:var(--navy);color:#fff;font-weight:700}
:root[data-theme="dark"] .rate button.on,
@media (prefers-color-scheme:dark){.rate button.on{background:var(--accent);border-color:var(--accent)}}
.rate button .k{font-size:8.5px;opacity:.5}
.empty{padding:16px 0;color:var(--ink-3);font-style:italic;font-size:13px}
footer{padding:30px 0 60px;color:var(--ink-3);font-size:12.5px;line-height:1.65;
       border-top:1px solid var(--rule);margin-top:32px}
footer code{font-family:var(--mono);font-size:11px;background:var(--raised);padding:1px 5px;
            border:1px solid var(--rule);border-radius:3px}
@media(max-width:720px){.row{grid-template-columns:4px 1fr;gap:10px}.sc,.rate .lbl{display:none}
  .rate{flex-direction:row;flex-wrap:wrap;grid-column:1/-1}}
</style>

<header><div class="wrap">
  <svg class="mark" viewBox="0 0 120 120" aria-hidden="true">
    <path d="M 82 42 A 22 22 0 1 0 60 64" fill="none" stroke="#f5a623" stroke-width="13"/>
    <path d="M 60 56 A 22 22 0 1 1 38 78" fill="none" stroke="#f5a623" stroke-width="13"/>
    <rect x="54" y="54" width="12" height="12" fill="#2f6fed"/>
  </svg>
  <span class="word">SIGNAL</span>
  <span class="sub">Rate today's intelligence</span>
  <span class="asof" id="asof"></span>
</div></header>

<div class="bar"><div class="wrap">
  <div class="prog">
    <div class="track"><div class="fill" id="fill"></div></div>
    <span class="n" id="pn">0 rated</span>
  </div>
  <select id="dom" onchange="render()"><option value="">All domains</option></select>
  <button class="btn" onclick="toggleCrit()" id="critBtn">Show criteria</button>
  <button class="btn primary" onclick="exportCsv()">Export ratings</button>
  <button class="btn" onclick="resetAll()">Reset</button>
</div></div>

<div class="crit" id="crit"><div class="wrap">
  <h3 id="critTitle"></h3><div class="crit-grid" id="critGrid"></div>
</div></div>

<main class="wrap" id="rows"></main>

<footer class="wrap">
  <p><b>Every headline is the publisher's own, verbatim, linked to the original.</b>
     Nothing here is generated — synthesis happens downstream in the newsletter.</p>
  <p style="margin-top:8px">Rate what you disagree with. Hover a row and press
     <b>1</b>–<b>5</b>, or click. Then <b>Export ratings</b> → save as
     <code>data/gold_set_review.csv</code> → <code>python scripts/merge_review.py</code>.</p>
  <p style="margin-top:8px">Twenty confident calls in one domain beat a hundred hesitant ones
     across all six.</p>
</footer>

<script>
const STORE=__STORE__, GUIDE=__GUIDE__;
const BANDS=[{k:"MUST_READ",l:"Must Read",v:"--sev-must",n:1},
             {k:"IMPORTANT",l:"Important",v:"--sev-imp",n:2},
             {k:"WATCH",l:"Watch",v:"--sev-watch",n:3},
             {k:"BACKGROUND",l:"Background",v:"--sev-bg",n:4},
             {k:"IGNORE",l:"Ignore",v:"--sev-bg",n:5}];
const KEY="signal_ratings_v1";
let mine=JSON.parse(localStorage.getItem(KEY)||"{}"), hovered=null;

const esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const bandOf=r=>mine[r.u]||r.b;
const meta=k=>BANDS.find(b=>b.k===k)||BANDS[3];

document.getElementById("asof").innerHTML="DATA AS OF <b>"+esc(STORE.data_date)+"</b>";
const sel=document.getElementById("dom");
[...new Set(STORE.rows.map(r=>r.d))].filter(Boolean).sort().forEach(d=>{
  const o=document.createElement("option"); o.value=d;
  o.textContent=(GUIDE[d]?GUIDE[d].display.split(" — ")[0]:d)+
    " ("+STORE.rows.filter(r=>r.d===d).length+")";
  sel.appendChild(o);
});

function toggleCrit(){
  const c=document.getElementById("crit"), open=c.classList.toggle("open");
  document.getElementById("critBtn").textContent=open?"Hide criteria":"Show criteria";
  if(open) renderCrit();
}
function renderCrit(){
  const d=sel.value||"insurance", g=GUIDE[d];
  document.getElementById("critTitle").textContent=g?g.display:"Criteria";
  document.getElementById("critGrid").innerHTML=BANDS.map(b=>{
    const c=g&&g.bands[b.k];
    return `<div class="crit-cell" style="--band:var(${b.v})">
      <div class="b">${b.l}</div>
      <div class="q">${esc(c?c.q:"")}</div>
      <div class="t">${esc(c?c.test:"")}</div></div>`;
  }).join("");
}

function render(){
  const filter=sel.value;
  const rows=STORE.rows.filter(r=>!filter||r.d===filter);
  const out=[];
  for(const b of BANDS.slice(0,4)){
    const inBand=rows.filter(r=>bandOf(r)===b.k);
    out.push(`<section style="--band:var(${b.v})">
      <div class="band-h"><h2>${b.l}</h2><span class="c">${inBand.length}</span></div>
      ${inBand.length?inBand.map(row).join(""):'<p class="empty">Nothing here.</p>'}</section>`);
  }
  const ign=rows.filter(r=>bandOf(r)==="IGNORE");
  if(ign.length) out.push(`<section style="--band:var(--sev-bg)">
    <div class="band-h"><h2>Ignore</h2><span class="c">${ign.length}</span></div>
    ${ign.map(row).join("")}</section>`);
  document.getElementById("rows").innerHTML=out.join("");
  const n=Object.keys(mine).length;
  document.getElementById("pn").textContent=n+" rated";
  document.getElementById("fill").style.width=Math.min(100,100*n/Math.max(1,rows.length))+"%";
  if(document.getElementById("crit").classList.contains("open")) renderCrit();
}

function row(r){
  const cur=bandOf(r), moved=mine[r.u]&&mine[r.u]!==r.b;
  const chips=[`<span class="chip">${esc(r.fb)}${r.age!=null?" · "+Math.round(r.age)+"h":""}</span>`,
    `<span class="chip ${r.tier==="tier_1"?"t1":""}">${esc(r.tier.replace("_"," "))}</span>`,
    ...r.evt.map(e=>`<span class="chip evt">${esc(e.replace(/_/g," "))}</span>`),
    ...r.ent.map(e=>`<span class="chip">${esc(e)}</span>`)].join("");
  const trace=r.why.map(w=>`<span class="s">${esc(w.s)}</span><span class="r">${esc(w.r)}</span>`).join("");
  const btns=BANDS.map(b=>`<button class="${cur===b.k?"on":""}"
      onclick="setBand('${esc(r.u)}','${b.k}')"><span class="k">${b.n}</span>${b.l}</button>`).join("");
  return `<article class="row ${moved?"rated":""}" data-u="${esc(r.u)}"
     onmouseenter="hovered='${esc(r.u)}'" onmouseleave="hovered=null">
    <div class="stripe"></div>
    <div class="sc tnum"><span class="v">${r.sc}</span><span class="l">score</span></div>
    <div>
      <div class="kick"><span class="dom">${esc(r.dn||r.d)}</span><span class="pub">${esc(r.p)}</span></div>
      <h4><a href="${esc(r.u)}" target="_blank" rel="noopener">${esc(r.t)}</a></h4>
      <div class="chips">${chips}</div>
      <details><summary>Why is it here?</summary><div class="trace">${trace}
        <span class="s">keywords</span><span class="r">${esc(r.ev.join(", ")||"—")}</span></div></details>
    </div>
    <div class="rate"><span class="lbl">Your call</span>${btns}</div>
  </article>`;
}

function setBand(u,b){ mine[u]=b; localStorage.setItem(KEY,JSON.stringify(mine)); render(); }
function resetAll(){ if(confirm("Clear all your ratings?")){mine={};localStorage.removeItem(KEY);render();} }

addEventListener("keydown",e=>{
  if(!hovered||e.metaKey||e.ctrlKey||/^(INPUT|SELECT|TEXTAREA)$/.test(e.target.tagName))return;
  const b=BANDS.find(x=>String(x.n)===e.key);
  if(b){ e.preventDefault(); setBand(hovered,b.k); }
});

function exportCsv(){
  const rows=[["index","draft_priority","your_priority","source","title","url"]];
  STORE.rows.forEach((r,i)=>{ const m=mine[r.u];
    if(m&&m!==r.b){ let h=""; try{h=new URL(r.u).hostname.replace(/^www\\./,"");}catch(e){}
      rows.push([i,r.b,m,h,r.t,r.u]); } });
  if(rows.length===1){alert("No changes yet — rate a few rows first.");return;}
  const csv=rows.map(r=>r.map(v=>'"'+String(v).replace(/"/g,'""')+'"').join(",")).join("\\n");
  const a=document.createElement("a");
  a.href=URL.createObjectURL(new Blob([csv],{type:"text/csv"}));
  a.download="gold_set_review.csv"; a.click();
}
render();
</script>"""


def main() -> int:
    store = compact(json.loads(STORE.read_text(encoding="utf-8")))
    html = (HTML.replace("__STORE__", json.dumps(store, ensure_ascii=False))
                .replace("__GUIDE__", json.dumps(guide_payload(), ensure_ascii=False)))
    OUT.write_text(html, encoding="utf-8")
    print(f"rows   : {len(store['rows'])}")
    print(f"wrote  : {OUT.relative_to(ROOT)}  ({OUT.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
