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
.pill {
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
.metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin: 12px 0 4px;
}
.metric {
  background: var(--panel);
  border: 1px solid var(--hair);
  border-radius: 10px;
  padding: 10px 12px;
}
.metric .n {
  font-size: 22px;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.03em;
  margin: 0;
}
.metric .lbl { font-weight: 600; margin: 0 0 2px; }
.metric .hint { color: var(--mute); font-size: 12px; margin: 0; }
@media (max-width: 700px) { .metrics { grid-template-columns: 1fr; } }
.kv th {
  width: 40%;
  color: var(--mute);
  font-weight: 500;
  text-transform: none;
  letter-spacing: 0;
  font-size: 13px;
}
.quota { display: flex; align-items: center; gap: 8px; justify-content: flex-end; }
.bar {
  display: inline-block;
  width: 72px;
  height: 6px;
  border-radius: 99px;
  background: var(--hair);
  overflow: hidden;
}
.bar i { display: block; height: 100%; background: var(--ok); }
.bar.warn i { background: var(--warn); }
.bar.bad i { background: var(--bad); }
.sub { color: var(--mute); font-size: 12px; margin-top: 2px; }
.devices-table { background: var(--panel); border: 1px solid var(--hair); border-radius: 10px; overflow: hidden; }
.devices-table table { margin: 0; }
.devices-table td { vertical-align: middle; padding: 10px 12px; }
.devices-table th { padding: 8px 12px; }
details.config > summary {
  cursor: pointer;
  color: var(--mute);
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  font-weight: 600;
  margin: 18px 0 8px;
}
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


def _format_limit(label: str, value: object) -> tuple[str, str]:
    text = str(value)
    pretty = {
        "Daily quota": ("Daily quota", f"{text} requests per device per day"),
        "Max text": ("Max selected text", f"{text} characters"),
        "Max extras": ("Max extra notes", f"{text} characters"),
        "Timestamp skew": ("Signature time window", text.replace("s", " seconds") if text.endswith("s") else text),
        "Nonce TTL": ("Nonce lifetime", text.replace("s", " seconds") if text.endswith("s") else text),
        "Devices / invite": ("Devices per invite", text if text == "unlimited" else f"{text} devices"),
        "Model": ("Model chain", text.replace(" → ", " → ")),
        "LLM base": ("LLM host", text),
        "LLM path": ("LLM path", text),
        "LLM timeout": ("LLM timeout", text.replace("s", " seconds") if str(text).endswith("s") else text),
        "LLM max tokens": ("Max tokens", text),
        "Temp / expand": ("Temperature (edit / expand)", text),
        "Require HTTPS": ("Require HTTPS", "On" if text == "yes" else "Off"),
        "Trust proxy": ("Trust proxy headers", "On" if text == "yes" else "Off"),
        "Invite tokens": ("Invite tokens", text),
        "Reset at": ("Quota resets", text.replace("T", " ").replace("+00:00", " UTC")),
        "Data path": ("Data file", text),
    }
    return pretty.get(label, (label, text))


def _quota_bar(used: int, limit: int) -> str:
    cls = _quota_class(used, limit)
    pct = 0 if limit <= 0 else min(100, round(100 * used / limit))
    bar_cls = f"bar {cls}".strip()
    return (
        f'<div class="quota"><span class="{cls}">{used} / {limit}</span>'
        f'<span class="{bar_cls}"><i style="width:{pct}%"></i></span></div>'
    )


def _model_state_class(state: str) -> str:
    if state == "available":
        return "ok"
    if state in {"timeout", "not configured"}:
        return "warn"
    return "bad"


def _short_model(model: str) -> str:
    name = (model or "").split("/")[-1]
    return name.replace(":free", "") or model


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
    limit_rows = []
    for item in limits:
        label, value = _format_limit(item["label"], item["value"])
        limit_rows.append(
            "<tr>"
            + f"<th>{escape(label)}</th>"
            + f"<td>{escape(value)}</td>"
            + "</tr>"
        )
    limits_html = "".join(limit_rows)
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
    device_rows = []
    for row in data["sessions"]:
        presence = str(row.get("presence") or "Away")
        name = escape(row["name"] or "Unnamed device")
        platform = escape(str(row.get("platform") or "Unknown client"))
        if row.get("live"):
            live_rows.append(
                "<tr>"
                + f"<td><strong>{name}</strong><div class=\"sub\">{platform}</div></td>"
                + _cell(row.get("seenAgo") or "just now")
                + f'<td>{_quota_bar(row["used"], row["limit"])}</td>'
                + "</tr>"
            )
        device_rows.append(
            "<tr>"
            + (
                f"<td title=\"{escape(row.get('id') or '')}\"><strong>{name}</strong>"
                f"<div class=\"sub\">{platform} · {escape(row.get('shortId') or '')}</div></td>"
            )
            + _cell(row.get("createdLabel") or "unknown")
            + _cell(row.get("lastSeenLabel") or row.get("seenAgo") or "never")
            + f'<td>{_quota_bar(row["used"], row["limit"])}</td>'
            + "</tr>"
        )

    live_html = (
        "<table><thead><tr><th>Device</th><th>Last active</th><th class=\"num\">Today</th></tr></thead>"
        f"<tbody>{''.join(live_rows)}</tbody></table>"
        if live_rows
        else '<p class="empty">No devices active in the last 2 minutes.</p>'
    )
    devices_html = (
        "<div class=\"devices-table\"><table><thead><tr>"
        "<th>Device</th><th>Registered</th><th>Last session</th><th class=\"num\">Today / limit</th>"
        f"</tr></thead><tbody>{''.join(device_rows)}</tbody></table></div>"
        if device_rows
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
    </div>
    <p class="meta">Model status checked UTC {models_checked}</p>
    <div class="metrics">
      <div class="metric">
        <p class="lbl">Active now</p>
        <p class="n">{live_n}</p>
        <p class="hint">Devices online in the last 2 minutes</p>
      </div>
      <div class="metric">
        <p class="lbl">Registered devices</p>
        <p class="n">{registered_n}</p>
        <p class="hint">Unique Macs that have joined this service</p>
      </div>
      <div class="metric">
        <p class="lbl">Requests today</p>
        <p class="n">{today_n}</p>
        <p class="hint">API calls since 00:00 UTC</p>
      </div>
    </div>

    <div class="split">
      <section class="panel">
        <h1>Active now</h1>
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

    <details class="config" open>
      <summary>Limits</summary>
      <div class="panel" style="padding:0 4px;">
        <table class="kv">
          <tbody>{limits_html}</tbody>
        </table>
      </div>
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
