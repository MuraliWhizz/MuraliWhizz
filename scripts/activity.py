"""Builds an animated neon contribution graph (last 30 days) -> dist/activity.svg
Runs inside GitHub Actions using the built-in GITHUB_TOKEN. No third-party service needed."""
import json, os, sys, datetime as dt, urllib.request

USER = os.environ.get("GH_USER", "MuraliWhizz")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = sys.argv[1] if len(sys.argv) > 1 else "dist/activity.svg"
DAYS = 30
MONO = "'Courier New','Consolas',monospace"

def fetch():
    q = """query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}"""
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": q, "variables": {"u": USER}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "activity-graph"})
    d = json.load(urllib.request.urlopen(req, timeout=30))
    weeks = d["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [x for w in weeks for x in w["contributionDays"]]
    return [(x["date"], x["contributionCount"]) for x in days][-DAYS:]

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;")

def build(data, note=""):
    W, H, L, R, T, B = 900, 300, 56, 30, 70, 50
    n = len(data)
    mx = max([c for _, c in data] + [4])
    mx = int(mx * 1.15) + 1
    cw, ch = W - L - R, H - T - B
    pts = [(L + cw * i / max(n - 1, 1), T + ch * (1 - c / mx)) for i, (_, c) in enumerate(data)]
    line = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = line + f" L{pts[-1][0]:.1f},{T+ch} L{pts[0][0]:.1f},{T+ch} Z"
    grid = "".join(f'<rect x="{L}" y="{T+ch*i/4:.1f}" width="{cw}" height="1" fill="#7b2ff7" fill-opacity=".25"/>'
                   f'<text x="{L-10}" y="{T+ch*i/4+4:.1f}" text-anchor="end" font-family="{MONO}" font-size="11" fill="#7b6fb5">{round(mx*(1-i/4))}</text>' for i in range(5))
    xl = "".join(f'<text x="{pts[i][0]:.1f}" y="{H-24}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="#7b6fb5">{data[i][0][5:]}</text>' for i in range(0, n, 5))
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="#fff" stroke="#ff2ec4" stroke-width="2"><animate attributeName="r" values="3;5;3" dur="2.4s" begin="{i*0.08:.2f}s" repeatCount="indefinite"/></circle>' for i, (x, y) in enumerate(pts) if data[i][1] > 0)
    total = sum(c for _, c in data)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<defs><linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7b2ff7" stop-opacity=".6"/><stop offset="1" stop-color="#7b2ff7" stop-opacity="0"/></linearGradient>
<linearGradient id="l" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#00f5ff"/><stop offset="1" stop-color="#ff2ec4"/></linearGradient>
<filter id="g" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
<style>.d{{stroke-dasharray:2400;stroke-dashoffset:2400;animation:dr 3s ease-out forwards}}@keyframes dr{{to{{stroke-dashoffset:0}}}}</style>
<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="16" fill="#0d0221" stroke="#7b2ff7" stroke-opacity=".6" stroke-width="2"/>
<text x="{L}" y="38" font-family="{MONO}" font-size="18" font-weight="bold" fill="#00f5ff">&gt; ACTIVITY_LOG // last {n} days</text>
<text x="{W-R}" y="38" text-anchor="end" font-family="{MONO}" font-size="14" fill="#ff2ec4">{total} contributions {esc(note)}</text>
{grid}{xl}
<path d="{area}" fill="url(#a)"/>
<path class="d" d="{line}" fill="none" stroke="url(#l)" stroke-width="3" stroke-linejoin="round" stroke-linecap="round" filter="url(#g)"/>
{dots}
</svg>'''

try:
    data = fetch()
    svg = build(data)
except Exception as e:
    print("fetch failed:", e, file=sys.stderr)
    today = dt.date.today()
    data = [((today - dt.timedelta(days=DAYS-1-i)).isoformat(), 0) for i in range(DAYS)]
    svg = build(data, "(data unavailable)")
os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
open(OUT, "w").write(svg)
print("wrote", OUT)
