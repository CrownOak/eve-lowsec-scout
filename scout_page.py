#!/usr/bin/env python3
"""
CROWN & OAK - Lowsec Scout : shared page renderer.
One source of truth for the "Top N safe mining systems" HTML, used both by the
static page lowsec_scout.py writes each run and by the optional scout_server.py.
"""
import html, os, tempfile

REFRESH_SECONDS = 60


def _fmt(v):
    return "" if v is None or v == "" else html.escape(str(v))


def render_page(state):
    """Return a full self-contained HTML document for the given payload dict
    ({generated_at, space, region, threat, snapshots_in_window, systems:[...]})."""
    if not state or not state.get("systems"):
        body = ('<div class="empty">No data yet. Run '
                '<code>lowsec_scout.py</code> to generate the page.</div>')
        sub = "waiting for first run"
    else:
        gen = _fmt(state.get("generated_at"))
        space = _fmt(state.get("space"))
        region = _fmt(state.get("region") or "all")
        snaps = _fmt(state.get("snapshots_in_window"))
        threat = ("zKill threat data included" if state.get("threat")
                  else "recorder snapshot (blank ZK does not mean zero kills)")
        sub = (f"space {space} &middot; region {region} &middot; "
               f"{snaps} snapshots in window &middot; {threat} &middot; "
               f"generated {gen} UTC")
        rows = []
        for i, s in enumerate(state["systems"], start=1):
            safe = s.get("safety", 0) or 0
            cls = "good" if safe >= 85 else "warn" if safe >= 50 else "bad"
            name = _fmt(s.get("name"))
            link = _fmt(s.get("dotlan") or
                        ("https://evemaps.dotlan.net/system/" + str(s.get("name", "")).replace(" ", "_")))
            rows.append(
                f"<tr><td class='rank'>{i}</td>"
                f"<td class='sys'><a href='{link}' target='_blank' rel='noopener'>{name}</a></td>"
                f"<td>{_fmt(s.get('sec'))}</td>"
                f"<td class='region'>{_fmt(s.get('region'))}</td>"
                f"<td class='num strong'>{_fmt(s.get('score'))}</td>"
                f"<td class='num {cls}'>{_fmt(safe)}</td>"
                f"<td class='num'>{_fmt(s.get('ore'))}</td>"
                f"<td class='num'>{_fmt(s.get('pvp1h'))}</td>"
                f"<td class='num'>{_fmt(s.get('jumps'))}</td>"
                f"<td class='num'>{_fmt(s.get('hist_avg_pvp'))}</td>"
                f"<td class='num'>{_fmt(s.get('samples'))}</td>"
                f"<td class='num'>{_fmt(s.get('zk_recent'))}</td>"
                f"<td class='num'>{_fmt(s.get('zk_last_h'))}</td></tr>")
        body = (
            "<table><thead><tr>"
            "<th>#</th><th>SYSTEM</th><th>SEC</th><th>REGION</th>"
            "<th>SCORE</th><th>SAFE</th><th>ORE</th><th>PVP1h</th><th>JUMP</th>"
            "<th>~AVG</th><th>N</th><th>ZK</th><th>LASTh</th>"
            "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="{REFRESH_SECONDS}">
<title>Crown &amp; Oak - Lowsec Scout</title>
<link rel="stylesheet" href="https://crownoak.github.io/wdeve/common.css?v=2"></head>
<body>
  <header>
    <h1>CROWN &amp; OAK &middot; LOWSEC SCOUT</h1>
    <div class="sub">{sub}</div>
  </header>
  <div class="wrap">{body}</div>
  <footer>Safe, ore-suitable CANDIDATES. No API exposes live ore anomalies; warp in and
  scan to confirm. Page auto-refreshes every {REFRESH_SECONDS}s.</footer>
<script src="https://crownoak.github.io/wdeve/nav.js"></script>
</body></html>"""


def write_html(path, state, password=None):
    """Atomically write render_page(state) to path. If password is given, the page
    is client-side encrypted (content readable only after entering it). Returns path."""
    text = render_page(state)
    if password:
        import page_lock
        text = page_lock.lock_page(text, password, title="Crown & Oak - Lowsec Scout")
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(suffix=".html", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except Exception:
        try: os.remove(tmp)
        except OSError: pass
        raise
    return path
