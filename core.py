"""Model loading, scoring and shared styling for the Drug Review Analytics app."""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
MODEL_DIR = ROOT / "models" / "run2"
DATA_DIR = ROOT / "data"
GROUPS = ["Low", "Middle", "High"]

NAVY, BLUE, CYAN, AQUA, ICE, CARD = "#0D47A1", "#1976D2", "#00ACC1", "#4DD0E1", "#E0F7FA", "#CCF1F6"
INK, MUTED = "#0B2545", "#34506A"
GROUP_COLOURS = {"Low": NAVY, "Middle": BLUE, "High": CYAN}


# ------------------------------------------------------------------ styling
# Colour roles (adapted from the AURA capstone): INK and MUTED carry text; BLUE marks data and focus;
# CYAN is for actions, active states and highlights, never body text; ICE and CARD only fill.
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Plus+Jakarta+Sans:wght@600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap');
:root{
  --navy:#0D47A1; --blue:#1976D2; --cyan:#00ACC1; --aqua:#4DD0E1; --ice:#E0F7FA; --card:#CCF1F6;
  --ink:#0B2545; --muted:#34506A; --line:rgba(13,71,161,.10); --track:rgba(13,71,161,.07);
  --shadow: 0 1px 2px rgba(13,71,161,.08), 0 6px 18px rgba(13,71,161,.07);
  --shadow-hi: 0 2px 4px rgba(13,71,161,.10), 0 14px 30px rgba(13,71,161,.11);
  --highlight: inset 0 1px 0 rgba(224,247,250,.95);
  --ease: cubic-bezier(.22,1,.36,1);
  --f-head:'Space Grotesk',sans-serif; --f-sub:'Plus Jakarta Sans',sans-serif; --f-body:'IBM Plex Sans',sans-serif; --f-num:'IBM Plex Mono',monospace;
}
html, body, .stMarkdown, p, li, label, input, textarea, button { font-family: var(--f-body); }
[data-testid="stIconMaterial"], .material-symbols-rounded { font-family: 'Material Symbols Rounded' !important; font-weight: normal; }
h1 { font-family: var(--f-head) !important; font-weight: 700 !important; color: var(--ink); letter-spacing: -0.015em; }
h2, h3, h4 { font-family: var(--f-sub) !important; font-weight: 600 !important; color: var(--ink); }
[data-testid="stMetricValue"], .num { font-family: var(--f-num) !important; font-variant-numeric: tabular-nums; }

/* Texture over flat palette colour: a fine dot grid gives the near-monochrome page depth without gradients. */
[data-testid="stApp"]{ background-color: var(--ice);
  background-image: radial-gradient(rgba(13,71,161,.08) 1px, transparent 1.2px); background-size: 18px 18px; background-attachment: fixed; }
[data-testid="stSidebar"]{ background-color: var(--card);
  background-image: radial-gradient(rgba(13,71,161,.07) 1px, transparent 1.2px); background-size: 16px 16px;
  border-right: 1px solid var(--line); box-shadow: inset -1px 0 0 rgba(224,247,250,.7); }
[data-testid="stSidebarNav"] a[aria-current="page"]{ background: rgba(224,247,250,.75) !important; box-shadow: inset 3px 0 0 var(--cyan), 0 1px 2px rgba(13,71,161,.08); }
.side-h{ font-family:var(--f-sub); font-size:.74rem; letter-spacing:.12em; text-transform:uppercase; color:var(--muted); margin:6px 0 2px; }

/* Page header: flat navy band with a light dot texture, a top highlight, a deep shadow and a cyan rule. Title only. */
.hero{ position:relative; overflow:hidden; border-radius:16px; padding:18px 28px; margin:0 0 18px; color:var(--ice);
  background-color: var(--navy); background-image: radial-gradient(rgba(224,247,250,.14) 1px, transparent 1.3px); background-size: 16px 16px;
  box-shadow: inset 0 1px 0 rgba(224,247,250,.30), var(--shadow-hi); border:1px solid rgba(11,37,69,.35); border-bottom: 6px solid var(--cyan); }
.hero .title{ font-family:var(--f-head); font-weight:700; font-size:1.95rem; line-height:1.15; margin:0; color:var(--ice); }

/* Room for the Streamlit Cloud toolbar: a solid, textured header so scrolled content passes under it, not through it. */
[data-testid="stHeader"]{ background-color: var(--ice) !important;
  background-image: radial-gradient(rgba(13,71,161,.08) 1px, transparent 1.2px); background-size: 18px 18px; background-attachment: fixed;
  border-bottom: 1px solid var(--line); }
[data-testid="stMainBlockContainer"], .block-container{ padding-top: 4.25rem !important; }

/* Cards: flat card colour, a top highlight, a solid accent edge, layered shadow and a hover lift. */
.card{ position:relative; background: var(--card); border:1px solid var(--line); border-radius:14px; padding:16px 20px; margin:8px 0 14px;
  box-shadow: var(--highlight), var(--shadow); transition: box-shadow .2s var(--ease), transform .2s var(--ease); }
.card::before{ content:""; position:absolute; left:16px; right:16px; top:-1px; height:3px; border-radius:0 0 3px 3px; background: var(--cyan); }
.card:hover{ box-shadow: var(--highlight), var(--shadow-hi); transform: translateY(-1px); }
.card .label{ color:var(--muted); font-size:.82rem; display:flex; align-items:center; gap:6px; }
.card .big{ font-family:var(--f-head); font-size:2rem; font-weight:700 !important; color:var(--ink); line-height:1.2; font-variant-numeric:tabular-nums; }
.card .sub{ color:var(--muted); font-size:.82rem; margin-top:2px; }
.kpis{ display:grid; grid-template-columns: repeat(var(--n,4), minmax(0,1fr)); gap:16px; margin: 4px 0 8px; }
@media (max-width: 1000px){ .kpis{ grid-template-columns: repeat(2, minmax(0,1fr)); } }
.kpi .big{ font-size:1.75rem; }
.kpi .ico{ display:inline-grid; place-items:center; width:30px; height:30px; border-radius:9px; margin-bottom:6px;
  background: rgba(224,247,250,.85); box-shadow: inset 0 0 0 1px var(--line); color:var(--navy); font-size:19px; }

.qt{ font-family:var(--f-sub); font-weight:600; font-size:1.12rem; color:var(--ink); margin:2px 0 8px; display:flex; align-items:center; gap:6px; }

/* Balanced rows: panels in one grid row share a height, the chart fills the middle and the note sits on the bottom edge. */
.row{ display:grid; grid-template-columns: repeat(var(--n,2), minmax(0,1fr)); gap:16px; align-items:stretch; margin:8px 0 16px; }
.row > .card{ margin:0; display:flex; flex-direction:column; }
.row > .card > .body{ flex:1; }
@media (max-width: 1000px){ .row{ grid-template-columns: minmax(0,1fr); } }

/* Panels that hold Streamlit elements (tables, Plotly, controls) wear the same card styling. */
[class*="st-key-card-"]{ position:relative; background: var(--card); border:1px solid var(--line); border-radius:14px; padding:16px 20px 18px;
  margin:8px 0 16px; box-shadow: var(--highlight), var(--shadow); }
[class*="st-key-card-"]::before{ content:""; position:absolute; left:16px; right:16px; top:-1px; height:3px; border-radius:0 0 3px 3px; background: var(--cyan); }
[class*="st-key-card-"] .qt{ margin-bottom:0; }
[class*="st-key-ctl-"]{ margin: 0 0 4px; }
[class*="st-key-ctl-"] label p{ font-size:.82rem; color:var(--muted); }

/* Word tags: navy for words typical of low ratings, aqua for high, matching the Low and High colours in the charts. */
.tags{ display:flex; flex-wrap:wrap; gap:6px; margin-top:6px; }
.tag{ display:inline-block; border-radius:6px; padding:3px 10px; font-size:.86rem; box-shadow: inset 0 1px 0 rgba(224,247,250,.3); }
.tag.low{ background:var(--navy); color:var(--ice); }
.tag.high{ background:var(--aqua); color:var(--ink); }
.tag.plain{ background:rgba(224,247,250,.9); color:var(--ink); box-shadow: inset 0 0 0 1px var(--line); }
.tag.absent{ text-decoration: line-through; color:var(--muted); }
.sublabel{ font-family:var(--f-sub); font-weight:600; font-size:.9rem; color:var(--ink); margin-top:4px; }
.split{ display:grid; grid-template-columns: 1fr 1fr; gap:24px; }
.cloud{ display:flex; flex-wrap:wrap; justify-content:center; align-items:center; gap:2px 16px; min-height:190px; padding:18px 16px;
  margin-top:8px; border-radius:12px; line-height:1.15; text-align:center; }
.cloud.low{ background:rgba(224,247,250,.85); color:var(--navy); box-shadow: inset 0 0 0 1px var(--line); }
.cloud.high{ background-color:var(--navy); color:var(--aqua); box-shadow: inset 0 1px 0 rgba(224,247,250,.25);
  background-image: radial-gradient(rgba(224,247,250,.10) 1px, transparent 1.3px); background-size: 14px 14px; }
.cloud{ flex-direction:column; } .cline{ display:flex; flex-wrap:wrap; justify-content:center; align-items:baseline; gap:2px 16px; }
.cloud span{ font-family:var(--f-head); letter-spacing:-0.01em; }
.terms{ width:100%; border-collapse:collapse; table-layout:fixed; background:rgba(224,247,250,.6); border-radius:10px; overflow:hidden; font-size:.86rem; }
.terms th, .terms td{ padding:9px 10px; text-align:left; vertical-align:top; border-bottom:1px solid rgba(13,71,161,.08); }
.terms thead th{ color:var(--muted); font-weight:500; font-size:.8rem; border-bottom:1px solid rgba(13,71,161,.16); }
.terms thead th:first-child, .terms tbody th{ width:190px; }
.terms tbody th{ font-family:var(--f-sub); font-weight:600; color:var(--ink); }
.terms tbody tr:nth-child(even){ background:rgba(204,241,246,.55); }
.terms .t{ color:var(--ink); line-height:1.3; }
.terms .n{ font-family:var(--f-num); font-size:.8rem; color:var(--muted); margin:2px 0 5px; font-variant-numeric:tabular-nums; }
.terms .track{ height:5px; border-radius:3px; background:var(--track); overflow:hidden; }
.terms .fill{ height:5px; border-radius:3px; background:var(--blue); }
.terms .fill.lead{ background:var(--navy); }
.disclaimer{ display:flex; align-items:center; gap:8px; margin:-4px 0 14px; color:var(--muted); font-size:.86rem; }
.disclaimer::before{ content:'info'; font-family:'Material Symbols Rounded'; font-size:18px; color:var(--blue); }
/* Panels side by side share one height; the note at the bottom of each lines up. */
[data-testid="stHorizontalBlock"]:has([class*="st-key-card-"]){ align-items:stretch; }
[data-testid="stColumn"]:has([class*="st-key-card-"]) > div{ height:100%; }
[data-testid="stColumn"] [data-testid="stLayoutWrapper"]:has(> [class*="st-key-card-"]){ height:100%; }
[data-testid="stColumn"] [class*="st-key-card-"]{ height:calc(100% - 16px); box-sizing:border-box; }
[class*="st-key-card-"] > [data-testid="stElementContainer"]:last-child:has(.note){ margin-top:auto; }
[class*="st-key-hd-"]{ margin-bottom:2px; }
[class*="st-key-hd-"] .qt{ margin:0; }
.scroll{ overflow-y:auto; padding-right:6px; }
.scroll::-webkit-scrollbar{ width:6px; } .scroll::-webkit-scrollbar-thumb{ background:rgba(13,71,161,.22); border-radius:3px; }

/* Centred bars (old dashboard): rated 1 to 3 or rated 1 reaches left, the high share right, the middle straddles the line. */
.dvhead{ display:flex; justify-content:center; gap:12px; margin-left:var(--lw,200px); color:var(--muted); font-size:.74rem; margin-bottom:4px; }
.dv{ display:flex; align-items:center; gap:10px; margin:5px 0; }
.dv .name{ width:var(--lw,200px); flex:none; text-align:right; color:var(--ink); font-size:.86rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.dvt{ position:relative; flex:1; height:18px; }
.dvt .axis{ position:absolute; left:50%; top:-4px; bottom:-4px; border-left:1px solid rgba(13,71,161,.25); }
.dvt b{ position:absolute; top:0; height:18px; }
.dvt b.lo{ background:var(--navy); border-radius:6px 0 0 6px; }
.dvt b.md{ background-color:var(--ice); background-image: repeating-linear-gradient(135deg, var(--cyan) 0 2.5px, transparent 2.5px 7px); box-shadow: inset 0 0 0 1px var(--cyan); }
.dvt b.hi{ background:var(--blue); border-radius:0 6px 6px 0; }
.dvt b.hi em{ position:absolute; right:6px; top:1px; font-style:normal; font-family:var(--f-num); font-size:.74rem; color:var(--ice); }
.dv:hover .name{ color:var(--blue); } .dv:hover .dvt{ filter:brightness(1.08); }

/* Dot plot (old dashboard): every medication on one axis from zero. */
.dt{ display:flex; align-items:center; gap:10px; margin:3px 0; }
.dt .name{ width:var(--lw,190px); flex:none; text-align:right; color:var(--ink); font-size:.86rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.dtt{ position:relative; flex:1; height:22px; }
.dtt i{ position:absolute; top:0; bottom:0; border-left:1px solid rgba(13,71,161,.10); }
.dtt b{ position:absolute; top:50%; width:10px; height:10px; margin:-5px 0 0 -5px; border-radius:50%; background:var(--navy); box-shadow:0 0 0 2px rgba(224,247,250,.9); }
.dt .pct{ width:44px; flex:none; text-align:right; font-family:var(--f-num); font-size:.82rem; color:var(--ink); }
.dtaxis .dtt{ height:16px; } .dtaxis .dtt span{ position:absolute; transform:translateX(-50%); font-family:var(--f-num); font-size:.72rem; color:var(--muted); }
.dt:hover .name{ color:var(--blue); } .dt:hover b{ background:var(--blue); }
.mark.m2{ border-left-style:dotted; border-left-color:var(--blue); } .mark.m2 span{ top:14px; color:var(--blue); }
.mark.m3{ border-left-style:solid; border-left-color:var(--cyan); } .mark.m3 span{ top:34px; }
.ladder .rung.lane1, .ladder .rung.lane3{ display:flex; flex-direction:column-reverse; } .ladder .rung.lane1 i, .ladder .rung.lane3 i{ margin:4px auto 0; }
.ladder .rung.lane1{ top:-50px; } .ladder .rung.lane3{ top:-88px; } .ladder .rung.lane2{ top:-9px; padding-top:58px; } .ladder .rung.lane2 i{ height:70px; margin-top:-58px; }
.ladder .rung small{ white-space:nowrap; }
.bandrow{ display:flex; align-items:center; gap:12px; } .bandrow > span{ width:96px; flex:none; text-align:right; color:var(--ink); font-size:.86rem; } .bandrow .stack{ flex:1; }
/* Hover details on bars, dots and segments: the same navy box as the info tooltips. First line is the item name. */
[data-tip]{ position:relative; }
[data-tip]:hover::after{ content:attr(data-tip); white-space:pre-line; position:absolute; z-index:60; left:min(var(--lw, 40%), 60%); bottom:calc(100% + 6px);
  min-width:170px; max-width:300px; padding:10px 12px; border-radius:10px; background:var(--navy); color:var(--ice); font-family:var(--f-body);
  font-size:.8rem; line-height:1.45; text-align:left; font-weight:400; box-shadow: inset 0 1px 0 rgba(224,247,250,.25), 0 12px 28px rgba(11,37,69,.28);
  pointer-events:none; }
.stack [data-tip]:hover::after{ left:0; }
.scroll [data-tip]:first-child:hover::after, .scroll [data-tip]:nth-child(2):hover::after{ bottom:auto; top:calc(100% + 6px); }
.cloud [data-tip]:hover::after{ left:50%; transform:translateX(-50%); min-width:0; white-space:nowrap; font-size:.76rem; }
.stack{ overflow:visible !important; } .stack > div[data-tip]{ overflow:visible !important; } .stack > div:first-child{ border-radius:9px 0 0 9px; } .stack > div:last-child{ border-radius:0 9px 9px 0; }
.dict{ width:100%; border-collapse:collapse; table-layout:fixed; background:rgba(224,247,250,.6); border-radius:10px; overflow:hidden; font-size:.9rem; }
.dict th, .dict td{ padding:10px 12px; text-align:left; vertical-align:top; border-bottom:1px solid rgba(13,71,161,.08); color:var(--ink); line-height:1.5; }
.dict thead th{ color:var(--muted); font-weight:500; font-size:.82rem; border-bottom:1px solid rgba(13,71,161,.16); }
.dict thead th:nth-child(1){ width:200px; } .dict thead th:nth-child(2){ width:160px; }
.dict tbody th code{ font-family:var(--f-num); font-size:.84rem; color:var(--navy); background:none; padding:0; }
.dict tbody tr:nth-child(even){ background:rgba(204,241,246,.55); }
.mini{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:14px; }
.mini > div{ background:rgba(224,247,250,.75); border-radius:10px; padding:10px 12px; box-shadow: inset 0 0 0 1px var(--line); }
.mini span{ display:block; color:var(--muted); font-size:.8rem; } .mini b{ display:block; font-family:var(--f-head); font-weight:700; font-size:1.25rem; color:var(--ink); line-height:1.25; }
.mini small{ color:var(--muted); font-size:.78rem; }
[class*="st-key-card-"] [data-testid="stPageLink"] a{ font-family:var(--f-sub); font-weight:600; color:var(--blue); }
.split3{ display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap:10px 24px; }
@media (max-width: 1000px){ .cloud{ display:flex; flex-wrap:wrap; justify-content:center; align-items:center; gap:2px 16px; min-height:190px; padding:18px 16px;
  margin-top:8px; border-radius:12px; line-height:1.15; text-align:center; }
.cloud.low{ background:rgba(224,247,250,.85); color:var(--navy); box-shadow: inset 0 0 0 1px var(--line); }
.cloud.high{ background-color:var(--navy); color:var(--aqua); box-shadow: inset 0 1px 0 rgba(224,247,250,.25);
  background-image: radial-gradient(rgba(224,247,250,.10) 1px, transparent 1.3px); background-size: 14px 14px; }
.cloud span{ font-family:var(--f-head); letter-spacing:-0.01em; }
.terms{ width:100%; border-collapse:collapse; table-layout:fixed; background:rgba(224,247,250,.6); border-radius:10px; overflow:hidden; font-size:.86rem; }
.terms th, .terms td{ padding:9px 10px; text-align:left; vertical-align:top; border-bottom:1px solid rgba(13,71,161,.08); }
.terms thead th{ color:var(--muted); font-weight:500; font-size:.8rem; border-bottom:1px solid rgba(13,71,161,.16); }
.terms thead th:first-child, .terms tbody th{ width:190px; }
.terms tbody th{ font-family:var(--f-sub); font-weight:600; color:var(--ink); }
.terms tbody tr:nth-child(even){ background:rgba(204,241,246,.55); }
.terms .t{ color:var(--ink); line-height:1.3; }
.terms .n{ font-family:var(--f-num); font-size:.8rem; color:var(--muted); margin:2px 0 5px; font-variant-numeric:tabular-nums; }
.terms .track{ height:5px; border-radius:3px; background:var(--track); overflow:hidden; }
.terms .fill{ height:5px; border-radius:3px; background:var(--blue); }
.terms .fill.lead{ background:var(--navy); }
.split3{ grid-template-columns: minmax(0,1fr); } }
.action{ margin-top:12px; color:var(--ink); }
.sec-h{ font-family:var(--f-head); font-weight:700; font-size:1.4rem; color:var(--ink); margin:22px 0 6px; padding-left:12px;
  box-shadow: inset 4px 0 0 var(--cyan); line-height:1.3; }
.action b{ font-family:var(--f-sub); }
.lead-in{ color:var(--muted); font-size:.88rem; margin:0 0 12px; }
.note{ margin-top:12px; padding:10px 14px; border-radius:10px; color:var(--ink); background: rgba(224,247,250,.7); box-shadow: inset 3px 0 0 var(--cyan); }

/* Bars and columns, solid palette colours */
.bar{ display:flex; align-items:center; gap:10px; margin:5px 0; }
.bar.tall{ margin:13.5px 0; }
.bar .name{ width:var(--lw, 64px); flex:none; color:var(--ink); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; font-size:.9rem; }
.bar .track{ flex:1; background:var(--track); border-radius:7px; height:14px; overflow:hidden; }
.bar .fill{ height:14px; border-radius:7px; background:var(--blue); }
.bar .fill.lead{ background:var(--navy); }
.bar .fill.other{ background:var(--aqua); }
.bar .pct{ width:var(--pw, 74px); flex:none; text-align:right; font-family:var(--f-num); color:var(--ink); font-size:.86rem; font-variant-numeric:tabular-nums; }
.stack{ display:flex; height:30px; border-radius:9px; overflow:hidden; box-shadow: inset 0 0 0 1px var(--line); }
.stack > div{ display:grid; place-items:center; font-family:var(--f-num); font-size:.8rem; color:var(--ice); white-space:nowrap; overflow:hidden; }
.stack.thin{ height:16px; border-radius:6px; }
.legend{ display:flex; gap:16px; flex-wrap:wrap; margin-top:8px; color:var(--muted); font-size:.84rem; align-items:center; }
.legend i{ display:inline-block; width:10px; height:10px; border-radius:3px; margin-right:6px; vertical-align:-1px; }
.cols{ position:relative; display:flex; align-items:flex-end; gap:8px; height:var(--h,190px); padding-top:18px; border-bottom:1px solid rgba(13,71,161,.18); }
.col{ flex:1; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; height:100%; }
.col .v{ font-family:var(--f-num); font-size:.76rem; color:var(--ink); margin-bottom:4px; white-space:nowrap; }
.col .c{ width:72%; border-radius:6px 6px 2px 2px; background:var(--blue); box-shadow: inset 0 1px 0 rgba(224,247,250,.35); }
.col .c.dark{ background:var(--navy); }
.col .c.soft{ background:var(--aqua); }
.colx{ display:flex; gap:8px; margin-top:6px; }
.colx > div{ flex:1; text-align:center; font-size:.76rem; color:var(--muted); }
.colx b{ display:block; color:var(--ink); font-weight:500; }
.mark{ position:absolute; bottom:0; top:8px; width:0; border-left:2px dashed var(--ink); }
.mark span{ position:absolute; top:-6px; left:4px; font-size:.72rem; color:var(--ink); background:rgba(224,247,250,.9); padding:0 4px; border-radius:4px; white-space:nowrap; }
.ladder{ position:relative; height:84px; margin:26px 8px 6px; border-top:2px solid rgba(13,71,161,.22); }
.rung{ position:absolute; top:-9px; transform:translateX(-50%); text-align:center; }
.rung i{ display:block; width:2px; height:16px; margin:0 auto 4px; background:var(--blue); }
.rung.strong i{ background:var(--navy); height:22px; }
.rung.up{ top:-50px; display:flex; flex-direction:column-reverse; }
.rung.up i{ margin:4px auto 0; }
.rung b{ display:block; font-family:var(--f-num); font-weight:500; font-size:.8rem; color:var(--ink); }
.rung small{ color:var(--muted); font-size:.72rem; }
.pair .fill.b{ background-color:var(--aqua); }

/* Pattern textures, as in the analyst report: they carry meaning, not decoration.
   .hatch  navy stripes on cyan with a navy outline: a comparison series next to a solid one, or "not yet evidence".
   .hatch-light  cyan stripes on ice: a wider or reference quantity (all other, the middle of the scale).
   .dotfill  cyan dots on ice: nothing there, or the smallest group. */
.hatch{ background-color:var(--aqua) !important; background-image: repeating-linear-gradient(135deg, rgba(13,71,161,.85) 0 2px, transparent 2px 6px) !important;
  box-shadow: inset 0 0 0 1.5px var(--navy); }
.hatch-light{ background-color:var(--ice) !important; background-image: repeating-linear-gradient(135deg, var(--cyan) 0 2.5px, transparent 2.5px 7px) !important;
  box-shadow: inset 0 0 0 1px var(--cyan); color:var(--ink) !important; }
.dotfill{ background-color:var(--ice) !important; background-image: radial-gradient(var(--cyan) 1.3px, transparent 1.5px) !important; background-size:7px 7px !important;
  box-shadow: inset 0 0 0 1px rgba(0,172,193,.55); color:var(--ink) !important; }
.bar .fill.other{ background-color:var(--ice); background-image: repeating-linear-gradient(135deg, var(--cyan) 0 2.5px, transparent 2.5px 7px); box-shadow: inset 0 0 0 1px var(--cyan); }
.pair .fill.b{ background-color:var(--aqua); background-image: repeating-linear-gradient(135deg, rgba(13,71,161,.85) 0 2px, transparent 2px 6px); box-shadow: inset 0 0 0 1.5px var(--navy); }
.empty{ padding:22px; border-radius:10px; text-align:center; color:var(--ink); background-color:var(--ice);
  background-image: radial-gradient(var(--cyan) 1.3px, transparent 1.5px); background-size:7px 7px; box-shadow: inset 0 0 0 1px rgba(0,172,193,.55); }
.stack .lbl{ background:rgba(224,247,250,.94); padding:0 6px; border-radius:5px; color:var(--ink); }
.empty span{ background:var(--ice); padding:2px 8px; border-radius:6px; }
.legend i.hatch, .legend i.hatch-light, .legend i.dotfill{ width:14px; height:12px; }

/* Probability bars on the prediction pages */
.pbar{ display:flex; align-items:center; gap:10px; margin:4px 0; }
.pbar .name{ width:64px; color:var(--ink); }
.pbar .track{ flex:1; background:var(--track); border-radius:7px; height:14px; overflow:hidden; }
.pbar .fill{ height:14px; border-radius:7px; }
.pbar .pct{ width:48px; text-align:right; font-family:var(--f-num); color:var(--ink); }
.chip{ display:inline-block; background:rgba(224,247,250,.9); box-shadow: inset 0 0 0 1px var(--line); color:var(--ink); border-radius:999px; padding:2px 10px; margin:2px 4px 2px 0; font-size:.85rem; }
.chip.absent{ text-decoration: line-through; color:var(--muted); }

/* Tooltips: hover or keyboard focus shows a definition, and "why it matters" when there is one. */
.tip{ position:relative; display:inline-grid; place-items:center; width:18px; height:18px; border-radius:50%; cursor:help;
  color:var(--blue); outline:none; vertical-align:middle; }
.tip .material-symbols-rounded{ font-size:17px; }
.tip .pop{ position:absolute; z-index:50; left:50%; bottom:calc(100% + 8px); transform:translate(-50%, 4px); width:280px;
  padding:12px 14px; border-radius:12px; background:var(--navy); color:var(--ice); border:1px solid rgba(11,37,69,.4);
  box-shadow: inset 0 1px 0 rgba(224,247,250,.25), 0 12px 32px rgba(11,37,69,.28); font-size:.82rem; line-height:1.45; text-align:left;
  text-transform:none; letter-spacing:0; font-weight:400; opacity:0; visibility:hidden; pointer-events:none;
  transition: opacity .15s var(--ease), transform .15s var(--ease), visibility 0s .15s; }
.tip .pop b{ display:block; font-family:var(--f-sub); color:var(--aqua); margin-bottom:4px; }
.tip .pop em{ display:block; font-style:normal; margin-top:6px; color:rgba(224,247,250,.82); }
.tip:hover .pop, .tip:focus .pop, .tip:focus-within .pop{ opacity:1; visibility:visible; transform:translate(-50%, 0); transition-delay:0s; }
.tip:focus-visible{ box-shadow: 0 0 0 2px var(--blue); }

/* Focus and interaction */
button:focus-visible, a:focus-visible, [tabindex]:focus-visible{ outline:2px solid var(--blue) !important; outline-offset:2px; }
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button{ background: var(--navy); border:0; box-shadow: inset 0 1px 0 rgba(224,247,250,.25), var(--shadow); }
.stButton > button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] > button:hover{ filter:brightness(1.12); }
[data-testid="stExpander"] details{ background:rgba(204,241,246,.75); border-radius:12px; box-shadow: var(--highlight); }
[data-testid="stDataFrame"]{ border-radius:12px; overflow:hidden; box-shadow: var(--shadow); }

/* Motion: rise on page open, pop for cards, bars grow left to right, columns grow upward. Off for reduced motion and print. */
@keyframes dra-rise{ from{ opacity:0; transform:translateY(12px); } to{ opacity:1; transform:none; } }
@keyframes dra-pop{ from{ opacity:0; transform:scale(.97); } to{ opacity:1; transform:none; } }
@keyframes dra-grow-right{ from{ clip-path: inset(0 100% 0 0); } to{ clip-path: inset(0 0 0 0); } }
@keyframes dra-grow-up{ from{ clip-path: inset(100% 0 0 0); } to{ clip-path: inset(0 0 0 0); } }
@media screen and (prefers-reduced-motion: no-preference){
  .hero{ animation: dra-rise .45s var(--ease) both; }
  .card{ animation: dra-pop .35s var(--ease) both; animation-delay: var(--d, 0s); }
  .bar .fill, .pbar .fill, .stack{ animation: dra-grow-right .6s var(--ease) both; animation-delay: var(--d, .1s); }
  .col .c{ animation: dra-grow-up .6s var(--ease) both; animation-delay: var(--d, .1s); }
}
@media (prefers-reduced-motion: reduce), print{ *{ animation:none !important; transition:none !important; } }
</style>"""


def style():
    st.markdown(CSS, unsafe_allow_html=True)


def tip(key):
    # An info icon that shows the definition on hover or keyboard focus.
    import html as _h
    from glossary import tip_parts
    title, what, why = (_h.escape(x, quote=True) for x in tip_parts(key))
    why_html = f"<em>{why}</em>" if why else ""
    return (f"<span class='tip' tabindex='0' aria-label=\"{title}: {what}\">"
            f"<span class='material-symbols-rounded'>info</span>"
            f"<span class='pop' role='tooltip'><b>{title}</b>{what}{why_html}</span></span>")


def kpi(label, value, sub="", key=None, icon="insights", delay=0.0):
    t = tip(key) if key else ""
    return (f"<div class='card kpi' style='--d:{delay:.2f}s'><div class='ico material-symbols-rounded'>{icon}</div>"
            f"<div class='label'>{label} {t}</div><div class='big'>{value}</div><div class='sub'>{sub}</div></div>")


def plot_layout(height, **extra):
    # Plotly charts styled like the HTML charts: same fonts, ink colour, transparent background inside a card.
    base = dict(height=height, margin=dict(l=8, r=8, t=8, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(224,247,250,.55)",
                font=dict(family="IBM Plex Sans", color=INK, size=13), hoverlabel=dict(bgcolor=NAVY, font_color=ICE, bordercolor=NAVY,
                font_family="IBM Plex Sans"), legend=dict(orientation="h", y=1.12, x=0, font=dict(color=MUTED)))
    base.update(extra)
    return base


def footer():
    # The footer line was removed in 0.4.0; kept as a no-op so older page code still runs.
    return None


def prob_bars(p, title):
    rows = "".join(f"<div class='pbar'><span class='name'>{g}</span><div class='track'>"
                   f"<div class='fill' style='width:{v * 100:.1f}%;background:{GROUP_COLOURS[g]};--d:{0.1 + i * 0.08:.2f}s'></div></div>"
                   f"<span class='pct'>{v * 100:.0f}%</span></div>" for i, (g, v) in enumerate(zip(GROUPS, p)))
    return f"<div class='label'>{title}</div><div class='big' style='margin-bottom:6px'>{GROUPS[int(np.argmax(p))]}</div>{rows}"


# ------------------------------------------------------------------ loading
def _json(path):
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else None


@st.cache_resource
def manifest():
    return _json(MODEL_DIR / "manifest.json")


@st.cache_resource
def preprocessing():
    return _json(MODEL_DIR / "preprocessing.json")


@st.cache_resource
def metrics():
    return _json(MODEL_DIR / "metrics.json")


@st.cache_resource
def categories():
    return _json(MODEL_DIR / "categories.json") or {"conditions": ["Unknown"], "medications": ["Unknown"]}


@st.cache_resource
def reviews_analysis():
    return _json(DATA_DIR / "reviews_analysis.json")


@st.cache_resource
def training_log():
    logs = sorted(DATA_DIR.glob("training_log_run*.json"))
    return _json(logs[-1]) if logs else None


def is_fragment(label):
    """A condition label that is really a piece of page text: it starts mid-word (lower case) or closes a bracket it never opened."""
    t = str(label).strip()
    if t.lower().startswith(("von ", "de ")):  # real names that start in lower case, such as von Willebrand's Disease
        return False
    return bool(t) and (t[0].islower() or (")" in t and "(" not in t))


@st.cache_data(show_spinner=False)
def _parquet(path, mtime):
    df = pd.read_parquet(path)
    if "condition_label" in df.columns:
        nr = (_json(DATA_DIR / "overview_meta.json") or {}).get("not_recorded_label", "Condition not recorded")
        frag = df["condition_label"].map(is_fragment)
        if frag.any():
            df = df.copy()
            df.loc[frag, "condition_label"] = nr
    return df


def data_parquet(name):
    # Loaded once per file version; a missing file is not cached, so copying it in works without a restart.
    p = DATA_DIR / name
    return _parquet(str(p), p.stat().st_mtime) if p.exists() else None


def overview_cube():
    return data_parquet("overview_cube.parquet")


def predictive_cube():
    return data_parquet("predictive_cube.parquet")


def overview_meta():
    return _json(DATA_DIR / "overview_meta.json")


@st.cache_resource
def tfidf_parts():
    import joblib
    vec = joblib.load(MODEL_DIR / "tfidf_vectoriser.joblib")
    model = joblib.load(MODEL_DIR / "objective1_fallback_model.joblib")
    return vec, model


@st.cache_resource
def bert_parts():
    # The compressed DistilBERT and its tokenizer; None when the run did not ship one.
    d = MODEL_DIR / "distilbert_onnx"
    if not (d / "model_int8.onnx").exists():
        return None
    import onnxruntime as ort
    from tokenizers import Tokenizer
    cfg = (preprocessing() or {}).get("objective1_onnx") or {}
    tok = Tokenizer.from_file(str(d / "tokenizer.json"))
    tok.enable_truncation(max_length=int(cfg.get("max_length", 256)))
    pad_id = tok.token_to_id("[PAD]")
    tok.enable_padding(pad_id=0 if pad_id is None else pad_id, pad_token="[PAD]")
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 2
    sess = ort.InferenceSession(str(d / "model_int8.onnx"), opts, providers=["CPUExecutionProvider"])
    return tok, sess


@st.cache_resource
def helpfulness_parts():
    import lightgbm as lgb
    booster = lgb.Booster(model_file=str(MODEL_DIR / "objective2_lightgbm.txt"))
    svd = None
    if (MODEL_DIR / "objective2_svd.joblib").exists() and (preprocessing() or {}).get("objective2_served") == "Structured + text":
        import joblib
        svd = joblib.load(MODEL_DIR / "objective2_svd.joblib")
    return booster, svd


def models_ready():
    return (MODEL_DIR / "manifest.json").exists()


# ------------------------------------------------------------------ scoring
def to_tokens(raw):
    # Rebuilds the NLP notebook's word list from the exported rules.
    cfg = preprocessing()
    t = str(raw).lower()
    for a, b in cfg["apostrophes"].items():
        t = t.replace(a, b)
    for pattern, repl in cfg["contractions"]:
        t = re.sub(pattern, repl, t)
    t = t.replace("'", "")
    stop = _stopwords()
    return " ".join(w for w in re.findall(cfg["word_pattern"], t) if w not in stop)


@st.cache_resource
def _stopwords():
    return frozenset(preprocessing()["stopwords"])


def tfidf_probs(texts):
    vec, model = tfidf_parts()
    X = vec.transform([to_tokens(t) for t in texts])
    if isinstance(model, dict):                      # ordinal fallback saved as its parts
        a = model["above_low"].predict_proba(X)[:, 1]
        b = np.minimum(model["above_middle"].predict_proba(X)[:, 1], a)
        p = np.column_stack([1 - a, a - b, b])
        return p / p.sum(1, keepdims=True)
    return model.predict_proba(X)


def bert_probs(texts, batch=32):
    tok, sess = bert_parts()
    texts = list(texts)
    order = np.argsort([len(t) for t in texts])
    out = np.zeros((len(texts), 3), dtype=np.float32)
    for i in range(0, len(texts), batch):
        idx = order[i:i + batch]
        enc = tok.encode_batch([texts[j] for j in idx])
        ids = np.array([e.ids for e in enc], dtype=np.int64)
        mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
        logits = sess.run(None, {"input_ids": ids, "attention_mask": mask})[0]
        e = np.exp(logits - logits.max(1, keepdims=True))
        out[idx] = e / e.sum(1, keepdims=True)
    return out


def served_name():
    cfg = preprocessing() or {}
    if bert_parts() is not None and str(cfg.get("objective1_served", "")).startswith("DistilBERT"):
        return cfg["objective1_served"]
    return cfg.get("objective1_fallback", "TF-IDF + LR")


def served_probs(texts):
    return bert_probs(texts) if served_name().startswith("DistilBERT") else tfidf_probs(texts)


def word_pushes(text, k=6):
    # Words that pushed the TF-IDF model toward Low or toward High (only for a plain logistic regression fallback).
    vec, model = tfidf_parts()
    if isinstance(model, dict):
        coef_low, coef_high = -model["above_low"].coef_[0], model["above_middle"].coef_[0]
    else:
        coef_low, coef_high = model.coef_[0], model.coef_[2]
    x = vec.transform([to_tokens(text)])
    if x.nnz == 0:
        return [], []
    vocab = vec.get_feature_names_out()
    low = [vocab[i] for i, c in sorted(zip(x.indices, coef_low[x.indices] * x.data), key=lambda z: -z[1])[:k] if c > 0]
    high = [vocab[i] for i, c in sorted(zip(x.indices, coef_high[x.indices] * x.data), key=lambda z: -z[1])[:k] if c > 0]
    return low, high


def helpfulness(text, rating, condition, medication):
    booster, svd = helpfulness_parts()
    cats = categories()
    cond = condition if condition in cats["conditions"] else "Unknown"
    med = medication if medication in cats["medications"] else "Unknown"
    f = pd.DataFrame({"rating": [float(rating)], "review_words": [float(len(str(text).split()))],
                      "condition": pd.Categorical([cond], categories=cats["conditions"]),
                      "medication": pd.Categorical([med], categories=cats["medications"])})
    if svd is not None:
        vec, _ = tfidf_parts()
        S = svd.transform(vec.transform([to_tokens(text)]))
        f = pd.concat([f, pd.DataFrame(S, columns=[f"text_{i}" for i in range(S.shape[1])])], axis=1)
    return float(booster.predict(f)[0]), cond, med
