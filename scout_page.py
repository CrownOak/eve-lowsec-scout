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
<style>
  :root {{ --ink:#14171c; --panel:#1b1f27; --line:#2a2f3a; --txt:#e8eaed; --mut:#9aa2af; --link:#7db1ff; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--ink); color:var(--txt);
         font:14px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; }}
  header {{ padding:22px 28px 14px; border-bottom:1px solid var(--line); }}
  h1 {{ margin:0; font-size:19px; letter-spacing:.06em; font-weight:700; }}
  .sub {{ color:var(--mut); margin-top:6px; font-size:12.5px; }}
  .wrap {{ padding:18px 28px 40px; }}
  table {{ border-collapse:collapse; width:100%; background:var(--panel);
           border:1px solid var(--line); border-radius:8px; overflow:hidden; }}
  th {{ text-align:left; background:#0f1217; color:#cdd3dc; font-size:11px;
        letter-spacing:.05em; text-transform:uppercase; padding:10px 12px; position:sticky; top:0; }}
  td {{ padding:9px 12px; border-top:1px solid var(--line); }}
  tr:hover td {{ background:#222732; }}
  .rank {{ color:var(--mut); width:34px; }}
  .sys a {{ color:var(--link); text-decoration:none; font-weight:600; }}
  .sys a:hover {{ text-decoration:underline; }}
  .region {{ color:var(--mut); }}
  .num {{ text-align:right; font-variant-numeric:tabular-nums; }}
  .strong {{ font-weight:700; }}
  .good {{ color:#7ddf8e; }} .warn {{ color:#e9c46a; }} .bad {{ color:#f08c84; }}
  .empty {{ padding:40px; text-align:center; color:var(--mut);
            background:var(--panel); border:1px solid var(--line); border-radius:8px; }}
  code {{ background:#0f1217; padding:2px 6px; border-radius:4px; color:#cdd3dc; }}
  footer {{ color:var(--mut); font-size:11.5px; padding:0 28px 30px; }}
</style></head>
<body>
  <header>
    <h1>CROWN &amp; OAK &middot; LOWSEC SCOUT</h1>
    <div class="sub">{sub}</div>
  </header>
  <div class="wrap">{body}</div>
  <footer>Safe, ore-suitable CANDIDATES. No API exposes live ore anomalies; warp in and
  scan to confirm. Page auto-refreshes every {REFRESH_SECONDS}s.</footer>
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
