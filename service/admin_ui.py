from html import escape
from urllib.parse import parse_qs

CSS = """
:root {
  --ink: #16130f;
  --paper: #f4efe6;
  --mute: #6e675c;
  --line: #16130f;
  --bad: #8f1d1d;
  --warn: #8a5a12;
  --ok: #1f4d32;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font: 13px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  background: var(--paper);
  color: var(--ink);
}
a { color: inherit; }
header, main, .auth { max-width: 1100px; margin: 0 auto; padding: 28px 22px; }
header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  border-bottom: 2px solid var(--line);
  padding-bottom: 16px;
}
header strong { font-size: 15px; letter-spacing: 0.12em; }
header span, .meta { color: var(--mute); }
h1 { font-size: 13px; letter-spacing: 0.16em; text-transform: uppercase; margin: 28px 0 10px; }
.limits {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1px;
  background: var(--line);
  border: 1px solid var(--line);
}
.limits div { background: var(--paper); padding: 12px 14px; }
.limits dt { color: var(--mute); font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; }
.limits dd { margin: 4px 0 0; font-size: 16px; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: 7px 8px; vertical-align: top; border-bottom: 1px solid var(--line); }
th { font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--mute); font-weight: 500; }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.bad { color: var(--bad); }
.warn { color: var(--warn); }
.ok { color: var(--ok); }
.empty { color: var(--mute); padding: 12px 0; }
.auth { max-width: 420px; padding-top: 18vh; }
label { display: block; margin-bottom: 8px; letter-spacing: 0.08em; text-transform: uppercase; font-size: 11px; }
input[type=password] {
  width: 100%;
  font: inherit;
  color: var(--ink);
  background: transparent;
  border: 0;
  border-bottom: 2px solid var(--line);
  padding: 8px 0;
  outline: none;
}
button {
  font: inherit;
  color: var(--paper);
  background: var(--ink);
  border: 0;
  padding: 8px 14px;
  margin-top: 18px;
  cursor: pointer;
}
.err { color: var(--bad); margin-top: 12px; }
.row { display: flex; justify-content: space-between; gap: 12px; }
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

    token_rows = []
    for row in data["tokens"]:
        token_rows.append(
            "<tr>"
            + _cell(row["name"])
            + _cell(row["ref"])
            + _cell(row["today"], "num")
            + _cell(row["total"], "num")
            + _cell(row["devices"], "num")
            + _cell(row["lastAt"] or "—")
            + "</tr>"
        )
    tokens_html = (
        "".join(token_rows)
        if token_rows
        else '<tr><td colspan="6" class="empty">No invite tokens configured.</td></tr>'
    )

    session_rows = []
    for row in data["sessions"]:
        cls = _quota_class(row["used"], row["limit"])
        session_rows.append(
            "<tr>"
            + _cell(row["name"] or "unnamed")
            + _cell(row["shortId"])
            + f'<td class="num {cls}">{row["used"]}/{row["limit"]}</td>'
            + _cell(row["tokenRef"] or "—")
            + _cell(row["lastSeenAt"] or row["createdAt"] or "—")
            + "</tr>"
        )
    sessions_html = (
        "".join(session_rows)
        if session_rows
        else '<tr><td colspan="5" class="empty">No devices registered yet.</td></tr>'
    )

    event_rows = []
    for row in data["events"]:
        cls = _status_class(int(row["status"]))
        event_rows.append(
            "<tr>"
            + _cell(row["at"])
            + _cell(row["path"])
            + _cell(row["action"])
            + f'<td class="num {cls}">{row["status"]}</td>'
            + _cell(row["latencyMs"], "num")
            + _cell(row["deviceName"] or row["shortId"] or "—")
            + _cell(row["tokenRef"] or "—")
            + "</tr>"
        )
    events_html = (
        "".join(event_rows)
        if event_rows
        else '<tr><td colspan="7" class="empty">No requests in this process yet.</td></tr>'
    )

    generated = escape(data["generatedAt"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="15">
  <title>Proovixy admin</title>
  <style>{CSS}</style>
</head>
<body>
  <header>
    <strong>PROOVIXY</strong>
    <span class="row">UTC {generated} · <a href="/admin/logout">sign out</a></span>
  </header>
  <main>
    <h1>Limits</h1>
    <dl class="limits">{limit_items}</dl>

    <h1>Tokens</h1>
    <table>
      <thead>
        <tr>
          <th>Token</th><th>Ref</th><th class="num">Today</th>
          <th class="num">Log</th><th class="num">Devices</th><th>Last seen</th>
        </tr>
      </thead>
      <tbody>{tokens_html}</tbody>
    </table>

    <h1>Sessions</h1>
    <table>
      <thead>
        <tr>
          <th>Device</th><th>Id</th><th class="num">Quota</th>
          <th>Token</th><th>Last seen</th>
        </tr>
      </thead>
      <tbody>{sessions_html}</tbody>
    </table>

    <h1>Request log</h1>
    <table>
      <thead>
        <tr>
          <th>Time</th><th>Path</th><th>Action</th><th class="num">Status</th>
          <th class="num">ms</th><th>Session</th><th>Token</th>
        </tr>
      </thead>
      <tbody>{events_html}</tbody>
    </table>
  </main>
</body>
</html>
"""
