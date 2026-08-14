from html import escape
from urllib.parse import parse_qs

CSS = """
:root {
  --ink: #1b1814;
  --paper: #f3efe7;
  --panel: #fbf8f2;
  --mute: #6f675c;
  --hair: #ddd4c6;
  --line: #cfc4b3;
  --bad: #9b2c2c;
  --warn: #8a5a12;
  --ok: #1f6b43;
  --live: #0f7a4a;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font: 13px/1.4 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  background: var(--paper);
  color: var(--ink);
}
a { color: inherit; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
header, main, .auth { max-width: 1080px; margin: 0 auto; padding: 18px 20px; }
header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding-bottom: 12px;
}
header strong { font-size: 13px; letter-spacing: 0.18em; }
header span, .meta { color: var(--mute); font-size: 12px; }
h1 {
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--mute);
  font-weight: 600;
  margin: 18px 0 8px;
}
.status {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  padding: 10px 0 4px;
  border-top: 1px solid var(--hair);
}
.pill, .stat {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--hair);
  background: var(--panel);
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
}
.pill i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--mute);
  display: inline-block;
}
.pill.ok i { background: var(--ok); }
.pill.warn i { background: var(--warn); }
.pill.bad i { background: var(--bad); }
.split {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 18px;
}
@media (max-width: 800px) { .split { grid-template-columns: 1fr; } }
.panel {
  background: var(--panel);
  border: 1px solid var(--hair);
  border-radius: 10px;
  padding: 4px 12px 10px;
}
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: 6px 6px; vertical-align: top; border-bottom: 1px solid var(--hair); }
th {
  font-size: 10px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--mute);
  font-weight: 600;
}
.num { text-align: right; font-variant-numeric: tabular-nums; }
.bad { color: var(--bad); }
.warn { color: var(--warn); }
.ok { color: var(--ok); }
.empty { color: var(--mute); padding: 10px 0; }
.auth { max-width: 420px; padding-top: 18vh; }
label { display: block; margin-bottom: 8px; letter-spacing: 0.08em; text-transform: uppercase; font-size: 11px; color: var(--mute); }
input[type=password] {
  width: 100%;
  font: inherit;
  color: var(--ink);
  background: transparent;
  border: 0;
  border-bottom: 1px solid var(--line);
  padding: 8px 0;
  outline: none;
}
button {
  font: inherit;
  color: var(--paper);
  background: var(--ink);
  border: 0;
  border-radius: 8px;
  padding: 7px 12px;
  margin-top: 18px;
  cursor: pointer;
}
.err { color: var(--bad); margin-top: 12px; }
.row { display: flex; justify-content: space-between; gap: 12px; align-items: center; }
.live-row, .device > summary {
  display: grid;
  grid-template-columns: 10px minmax(90px, 1.2fr) minmax(90px, 1fr) 72px 70px;
  gap: 10px;
  align-items: center;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--mute);
}
.dot.live { background: var(--live); box-shadow: 0 0 0 3px rgba(15, 122, 74, 0.15); }
.dot.idle { background: var(--warn); }
.devices { border: 1px solid var(--hair); border-radius: 10px; background: var(--panel); overflow: hidden; }
.device { border-bottom: 1px solid var(--hair); }
.device:last-child { border-bottom: 0; }
.device > summary {
  list-style: none;
  cursor: pointer;
  padding: 8px 12px;
}
.device > summary::-webkit-details-marker { display: none; }
.device .name { font-weight: 600; }
.device .id, .facts .mono { color: var(--mute); font-size: 12px; }
.facts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 6px 16px;
  padding: 0 12px 12px 30px;
  color: var(--mute);
  font-size: 12px;
}
.limits {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1px;
  background: var(--hair);
  border: 1px solid var(--hair);
  border-radius: 10px;
  overflow: hidden;
}
.limits div { background: var(--panel); padding: 10px 12px; }
.limits dt { color: var(--mute); font-size: 10px; letter-spacing: 0.08em; text-transform: uppercase; }
.limits dd { margin: 3px 0 0; font-size: 15px; }
details.config > summary {
  cursor: pointer;
  list-style: none;
  color: var(--mute);
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  font-weight: 600;
  margin: 18px 0 8px;
}
details.config > summary::-webkit-details-marker { display: none; }
.log-toolbar { margin-bottom: 6px; }
.log-toolbar button { margin-top: 0; padding: 5px 10px; font-size: 12px; }
.log-scroll {
  max-height: 240px;
  overflow: auto;
  border: 1px solid var(--hair);
  border-radius: 10px;
  background: var(--panel);
}
.log-scroll table { margin: 0; }
.log-scroll thead th {
  position: sticky;
  top: 0;
  background: var(--panel);
  z-index: 1;
}
.log-scroll .empty { padding: 12px 8px; }
"""


def token_ref(token: str) -> str:
    import hashlib

    return hashlib.sha256(f"proovixy-token:{token}".encode("utf-8")).hexdigest()[:8]


def parse_form_token(body: bytes) -> str:
    parsed = parse_qs(body.decode("utf-8"), keep_blank_values=True)
    values = parsed.get("token") or []
    return values[0] if values else ""


def _cell(value: object, cls: str = "") -> str:
    text = escape(str(value if value is not None else "—"))
    attr = f' class="{cls}"' if cls else ""
    return f"<td{attr}>{text}</td>"


def _quota_class(used: int, limit: int) -> str:
    if limit <= 0:
        return ""
    ratio = used / limit
    if used >= limit:
        return "bad"
    if ratio >= 0.8:
        return "warn"
    return ""


def _status_class(status: int) -> str:
    if status >= 500:
        return "bad"
    if status >= 400:
        return "warn"
    return "ok"


def _model_state_class(state: str) -> str:
    if state == "available":
        return "ok"
    if state in {"timeout", "not configured"}:
        return "warn"
    return "bad"


def _short_model(model: str) -> str:
    name = (model or "").split("/")[-1]
    return name.replace(":free", "") or model


def _dot_class(presence: str) -> str:
    if presence == "Live":
        return "live"
    if presence == "Idle":
        return "idle"
    return ""


def render_login(error: str = "") -> str:
    err = f'<p class="err">{escape(error)}</p>' if error else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Proovixy admin</title>
  <style>{CSS}</style>
</head>
<body>
  <form class="auth" method="post" action="/admin/login">
    <header style="padding:0 0 16px; margin-bottom:28px;">
      <strong>PROOVIXY</strong>
      <span>admin</span>
    </header>
    <label for="token">Admin token</label>
    <input id="token" name="token" type="password" autocomplete="current-password" autofocus>
    <button type="submit">Open</button>
    {err}
  </form>
</body>
</html>
"""


def render_dashboard(data: dict) -> str:
    limits = data["limits"]
    limit_items = "".join(
        f"<div><dt>{escape(item['label'])}</dt><dd>{escape(str(item['value']))}</dd></div>"
        for item in limits
    )
    health = data.get("health") or {}
    api_cls = "ok" if health.get("api") == "ok" else "bad"
    storage_state = str(health.get("storage") or "unknown")
    storage_cls = "ok" if storage_state == "ok" else "warn"

    model_pills = []
    for row in data.get("models") or []:
        cls = _model_state_class(str(row.get("state") or ""))
        label = row.get("role") or "Model"
        short = _short_model(str(row.get("model") or ""))
        title = escape(f"{row.get('model') or ''} · {row.get('state') or ''} · {row.get('detail') or ''}")
        model_pills.append(
            f'<span class="pill {cls}" title="{title}"><i></i>{escape(str(label))} · {escape(short)}</span>'
        )
    if not model_pills:
        model_pills.append('<span class="pill warn"><i></i>Models unchecked</span>')
    models_checked = escape(str(data.get("modelsCheckedAt") or "—"))

    token_rows = []
    for row in data["tokens"]:
        token_rows.append(
            "<tr>"
            + _cell(row["name"])
            + _cell(row["ref"], "mono")
            + _cell(row["today"], "num")
            + _cell(row["devices"], "num")
            + _cell(row["lastAt"] or "—")
            + "</tr>"
        )
    tokens_html = (
        "".join(token_rows)
        if token_rows
        else '<tr><td colspan="5" class="empty">No invite tokens configured.</td></tr>'
    )

    live_rows = []
    device_items = []
    for row in data["sessions"]:
        presence = str(row.get("presence") or "Away")
        qcls = _quota_class(row["used"], row["limit"])
        summary = (
            f'<span class="dot {_dot_class(presence)}"></span>'
            f'<span class="name">{escape(row["name"] or "Unnamed")}</span>'
            f'<span class="id mono">{escape(row.get("shortId") or "—")}</span>'
            f'<span class="num {qcls}">{row["used"]}/{row["limit"]}</span>'
            f'<span class="meta">{escape(str(row.get("seenAgo") or "—"))}</span>'
        )
        if row.get("live"):
            live_rows.append(f'<div class="live-row">{summary}</div>')
        facts = [
            ("Status", row.get("status") or "Active"),
            ("Client", row.get("platform") or "Unknown client"),
            ("Invite", f"{row.get('tokenName') or 'unknown'} ({row.get('tokenRef') or '—'})"),
            ("Registered", row.get("createdLabel") or "unknown"),
            ("Last seen", row.get("lastSeenLabel") or "never"),
            ("Quota", row.get("quotaLabel") or f'{row["used"]}/{row["limit"]}'),
            ("Resets", row.get("resetLabel") or "—"),
            ("Device ID", row.get("id") or "—"),
        ]
        if row.get("lastIp"):
            facts.append(("Last IP", row["lastIp"]))
        if row.get("userAgent"):
            facts.append(("User-Agent", row["userAgent"]))
        fact_html = "".join(
            f"<div><strong>{escape(str(label))}</strong><div class=\"mono\">{escape(str(value))}</div></div>"
            for label, value in facts
        )
        device_items.append(
            f"<details class=\"device\"><summary>{summary}</summary>"
            f"<div class=\"facts\">{fact_html}</div></details>"
        )

    live_html = (
        "".join(live_rows)
        if live_rows
        else '<p class="empty">No devices active in the last 2 minutes.</p>'
    )
    devices_html = (
        f'<div class="devices">{"".join(device_items)}</div>'
        if device_items
        else '<p class="empty">No devices registered yet.</p>'
    )

    event_rows = []
    for row in data["events"]:
        cls = _status_class(int(row["status"]))
        event_rows.append(
            "<tr"
            + f' data-at="{escape(str(row["at"]))}"'
            + ">"
            + _cell(row["at"], "mono")
            + _cell(row["path"])
            + _cell(row["action"])
            + f'<td class="num {cls}">{row["status"]}</td>'
            + _cell(row["latencyMs"], "num")
            + _cell(row["deviceName"] or row["shortId"] or "—")
            + _cell(row["tokenRef"] or "—", "mono")
            + "</tr>"
        )
    events_html = (
        "".join(event_rows)
        if event_rows
        else '<tr><td colspan="7" class="empty">No requests in this process yet.</td></tr>'
    )

    generated = escape(data["generatedAt"])
    live_n = escape(str(health.get("live", 0)))
    registered_n = escape(str(health.get("registered", 0)))
    today_n = escape(str(health.get("requestsToday", 0)))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="30">
  <title>Proovixy admin</title>
  <style>{CSS}</style>
</head>
<body>
  <header>
    <strong>PROOVIXY</strong>
    <span class="row">UTC {generated} · <a href="/admin">Refresh</a> · <a href="/admin/logout">sign out</a></span>
  </header>
  <main>
    <div class="status">
      <span class="pill {api_cls}"><i></i>API</span>
      <span class="pill {storage_cls}"><i></i>Storage · {escape(storage_state)}</span>
      {''.join(model_pills)}
      <span class="stat">{live_n} live</span>
      <span class="stat">{registered_n} devices</span>
      <span class="stat">{today_n} today</span>
    </div>
    <p class="meta">Models checked UTC {models_checked}</p>

    <div class="split">
      <section class="panel">
        <h1>Live</h1>
        {live_html}
      </section>
      <section class="panel">
        <h1>Invites</h1>
        <table>
          <thead>
            <tr>
              <th>Token</th><th>Ref</th><th class="num">Today</th>
              <th class="num">Devices</th><th>Last seen</th>
            </tr>
          </thead>
          <tbody>{tokens_html}</tbody>
        </table>
      </section>
    </div>

    <h1>Devices</h1>
    {devices_html}

    <h1>Request log</h1>
    <div class="log-toolbar row">
      <p class="meta">Scroll stays in this window. Clear hides rows here only — server history is kept.</p>
      <button type="button" id="clear-log">Clear window</button>
    </div>
    <div class="log-scroll" id="log-scroll">
      <table>
        <thead>
          <tr>
            <th>Time</th><th>Path</th><th>Action</th><th class="num">Status</th>
            <th class="num">ms</th><th>Session</th><th>Token</th>
          </tr>
        </thead>
        <tbody id="log-body">{events_html}</tbody>
      </table>
    </div>

    <details class="config">
      <summary>Limits</summary>
      <dl class="limits">{limit_items}</dl>
    </details>
  </main>
  <script>
    (function () {{
      var KEY = "proovixyLogHideUntil";
      var SCROLL = "proovixyLogScroll";
      var box = document.getElementById("log-scroll");
      var body = document.getElementById("log-body");
      var button = document.getElementById("clear-log");
      if (!box || !body) return;

      function newestStamp() {{
        var row = body.querySelector("tr[data-at]");
        return row ? row.getAttribute("data-at") : "";
      }}

      function applyHide() {{
        var until = sessionStorage.getItem(KEY) || "";
        if (!until) return;
        body.querySelectorAll("tr[data-at]").forEach(function (row) {{
          if ((row.getAttribute("data-at") || "") <= until) row.remove();
        }});
        if (!body.querySelector("tr[data-at]")) {{
          body.innerHTML = '<tr><td colspan="7" class="empty">Log window cleared. Server history is unchanged.</td></tr>';
        }}
      }}

      applyHide();
      box.scrollTop = Number(sessionStorage.getItem(SCROLL) || 0);
      box.addEventListener("scroll", function () {{
        sessionStorage.setItem(SCROLL, String(box.scrollTop));
      }});
      if (button) {{
        button.addEventListener("click", function () {{
          sessionStorage.setItem(KEY, newestStamp());
          sessionStorage.setItem(SCROLL, "0");
          applyHide();
          box.scrollTop = 0;
        }});
      }}
    }})();
  </script>
</body>
</html>
"""
