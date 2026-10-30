import json
import os
import tempfile

from flask import Flask, jsonify, render_template_string, request

from main import FILE, PROVIDERS, get_ai_suggestions

app = Flask(__name__)

PAGE = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CampusFlow – IT help desk</title>
  <link rel="icon" href="data:,">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
  {% raw %}
  <style>
    :root {
      --void: #070B16;
      --panel: #0F1424;
      --inset: #0A0F1D;
      --line: #232B45;
      --text: #E7EAF3;
      --muted: #8791AD;
      --mint: #6EE7A8;
      --blue: #7AA2FF;
      --signal: #FFFFFF;
      --ink: #11141F;
      --red: #FF7A85;
      --ui: "Bricolage Grotesque", system-ui, sans-serif;
      --mono: "JetBrains Mono", ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
    }
    * { box-sizing: border-box; }
    html, body { margin: 0; }
    body {
      background: var(--void);
      color: var(--text);
      font-family: var(--ui);
      font-size: 16px;
      line-height: 1.55;
      padding: 32px 16px 56px;
    }

    .window {
      max-width: 880px;
      margin: 0 auto;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      overflow: hidden;
      box-shadow: 0 30px 80px rgba(0, 0, 0, 0.45);
    }
    .bar {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 18px;
      border-bottom: 1px solid var(--line);
      font-family: var(--mono);
      font-size: 12.5px;
      color: var(--muted);
    }
    .dot { width: 11px; height: 11px; border-radius: 50%; display: inline-block; }
    .dot.r { background: #ff5f57; }
    .dot.y { background: #febc2e; }
    .dot.g { background: #28c840; }
    .bar .name { margin-left: 8px; }

    main { padding: 40px 36px 40px; }
    @media (max-width: 640px) { main { padding: 28px 18px 32px; } }

    h1 {
      font-family: var(--ui);
      font-weight: 700;
      font-size: clamp(30px, 5.2vw, 46px);
      line-height: 1.08;
      letter-spacing: -0.025em;
      margin: 0 0 12px;
      display: grid;
    }
    h1 > span { grid-area: 1 / 1; }
    .ghost { visibility: hidden; }
    .caret {
      display: inline-block;
      width: 0.55em;
      height: 1em;
      margin-left: 4px;
      vertical-align: -0.12em;
      background: var(--mint);
      animation: blink 1.1s steps(1) infinite;
    }
    @keyframes blink { 50% { opacity: 0; } }
    @media (prefers-reduced-motion: reduce) { .caret { animation: none; } }

    .lede { color: var(--muted); font-size: 17px; max-width: 52ch; margin: 0 0 30px; }

    .term-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-family: var(--mono);
      font-size: 13px;
      color: var(--muted);
      margin-bottom: 10px;
    }
    .clear {
      background: transparent;
      border: 0;
      color: var(--muted);
      font: inherit;
      cursor: pointer;
      padding: 4px 6px;
      border-radius: 6px;
    }
    .clear:hover { color: var(--text); }
    .clear:focus-visible { outline: 3px solid var(--blue); }

    .term {
      background: var(--inset);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 20px 22px 24px;
      min-height: 260px;
      cursor: text;
      font-family: var(--mono);
      font-size: 14.5px;
      line-height: 1.6;
    }
    .term:focus-within { border-color: #2F3A5E; }
    .entry {
      margin-top: 12px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }
    .entry:first-child { margin-top: 0; }
    .spacer { height: 22px; }

    .input-row { display: flex; flex-wrap: wrap; align-items: flex-start; margin-top: 12px; }
    .input-row[hidden] { display: none; }
    .prompt { white-space: pre-wrap; max-width: 100%; }
    #input {
      flex: 1 1 12ch;
      min-width: 12ch;
      background: transparent;
      border: 0;
      outline: 0;
      padding: 0;
      margin: 0;
      color: #ffffff;
      font: inherit;
      resize: none;
      overflow: hidden;
      caret-color: var(--mint);
      caret-shape: block;
    }

    .mint { color: var(--mint); }
    .blue { color: var(--blue); font-weight: 700; }
    .bgreen { color: #4ade80; font-weight: 700; }
    .yellow { color: #ffd43b; }
    .red { color: var(--red); }
    .muted { color: var(--muted); }
    .white { color: #ffffff; }

    .opt { cursor: pointer; border-radius: 6px; }
    .opt:hover { background: #121A33; }

    .ticket {
      background: var(--signal);
      color: var(--ink);
      border-radius: 16px;
      padding: 22px 26px 20px;
      margin-top: 16px;
      font-family: var(--ui);
      white-space: normal;
    }
    .ticket-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; flex-wrap: wrap; }
    .ticket-id {
      display: inline-block;
      margin: 0 0 6px;
      padding: 2px 8px;
      border-radius: 6px;
      background: var(--ink);
      color: var(--signal);
      font-family: var(--mono);
      font-weight: 700;
      font-size: 13px;
    }
    .ticket h3 { margin: 0; font-size: 22px; line-height: 1.2; letter-spacing: -0.015em; }
    .ticket-by { margin: 0; font-family: var(--mono); font-size: 12.5px; color: #4A4F5E; text-align: right; }
    @media (max-width: 640px) { .ticket-by { text-align: left; } }

    .tear { position: relative; border-top: 2px dashed rgba(17, 20, 31, 0.4); margin: 20px -26px; }
    .tear::before, .tear::after {
      content: "";
      position: absolute;
      top: -11px;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: var(--inset);
    }
    .tear::before { left: -10px; }
    .tear::after { right: -10px; }

    .steps { list-style: none; margin: 0; padding: 0; display: grid; gap: 14px; font-size: 16px; font-weight: 500; }
    .step { display: flex; gap: 14px; align-items: flex-start; cursor: pointer; position: relative; }
    .step input { position: absolute; opacity: 0; width: 22px; height: 22px; margin: 0; left: 0; top: 2px; }
    .box {
      flex: none;
      width: 22px;
      height: 22px;
      margin-top: 2px;
      border: 2px solid var(--ink);
      border-radius: 6px;
      display: grid;
      place-items: center;
    }
    .step input:checked ~ .box { background: var(--ink); }
    .step input:checked ~ .box::after { content: "✔"; color: var(--signal); font-size: 13px; line-height: 1; }
    .step input:checked ~ .text { opacity: 0.55; text-decoration: line-through; }
    .step input:focus-visible ~ .box { outline: 3px solid var(--blue); outline-offset: 3px; }

    .ticket-foot { display: flex; justify-content: flex-end; margin-top: 20px; }
    .copy {
      background: var(--ink);
      color: var(--signal);
      border: 0;
      border-radius: 8px;
      padding: 8px 14px;
      font-family: var(--mono);
      font-size: 13px;
      cursor: pointer;
    }
    .copy:focus-visible { outline: 3px solid var(--blue); outline-offset: 3px; }
  </style>
  {% endraw %}
</head>
<body>
  <div class="window">
    <div class="bar">
      <span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
      <span class="name">student@campusflow: ~/help-desk</span>
    </div>

    <main>
      <h1 aria-label="What’s broken on campus?">
        <span class="ghost" aria-hidden="true">What’s broken on campus?</span>
        <span aria-hidden="true"><span id="typed">What’s broken on campus?</span><span class="caret"></span></span>
      </h1>
      <p class="lede">Answer the prompts below. CampusFlow saves a ticket and asks an AI assistant for fixes you can try right now.</p>

      <noscript><p class="lede">This page needs JavaScript to run.</p></noscript>

      <div class="term-head">
        <span>session</span>
        <button class="clear" id="clear" type="button">clear</button>
      </div>
      <div class="term" id="term">
        <div id="entries" role="log" aria-live="polite"></div>
        <div class="input-row" id="row" hidden>
          <span class="prompt" id="prompt"></span>
          <textarea id="input" rows="1" autocomplete="off" autocapitalize="off" autocorrect="off" spellcheck="false" aria-label="Terminal input"></textarea>
        </div>
      </div>
    </main>
  </div>

  <script>window.CAMPUSFLOW = {{ data|tojson }};</script>
  {% raw %}
  <script>
  (function () {
    var DATA = window.CAMPUSFLOW.providers;
    var FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏";
    var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    var term = document.getElementById("term");
    var entries = document.getElementById("entries");
    var row = document.getElementById("row");
    var promptEl = document.getElementById("prompt");
    var input = document.getElementById("input");

    var resolver = null;
    var pendingLabel = "";
    var currentMenu = null;
    var menuCount = 0;
    var history = [];
    var historyIndex = 0;

    // ---------- Typed headline ----------
    (function typeHeadline() {
      if (reduceMotion) { return; }
      var typed = document.getElementById("typed");
      var text = typed.textContent;
      typed.textContent = "";
      var i = 0;
      (function tick() {
        if (i < text.length) {
          typed.textContent += text.charAt(i);
          i += 1;
          setTimeout(tick, 38);
        }
      })();
    })();

    // ---------- Small DOM helpers ----------
    function make(tag, cls, text) {
      var node = document.createElement(tag);
      if (cls) { node.className = cls; }
      if (text !== undefined) { node.textContent = text; }
      return node;
    }

    function makeLine(parts) {
      var div = make("div", "entry");
      parts.forEach(function (p) { div.appendChild(make("span", p[1], p[0])); });
      return div;
    }

    function reveal(node) {
      node.scrollIntoView({ block: "nearest", behavior: reduceMotion ? "auto" : "smooth" });
    }

    function addEntry(node) {
      entries.appendChild(node);
      reveal(node);
      return node;
    }

    function errorEntry(message, ticketSaved) {
      var wrap = make("div");
      wrap.appendChild(makeLine([["✖ " + message, "red"]]));
      if (ticketSaved) {
        wrap.appendChild(makeLine([["Your ticket is saved.", "muted"]]));
      }
      return wrap;
    }

    function parseSteps(text) {
      var steps = [];
      text.split("\n").forEach(function (line) {
        line = line.trim().replace(/\*\*/g, "").replace(/^(\d+[.)]|[-*•])\s*/, "");
        if (line) { steps.push(line); }
      });
      return steps;
    }

    function clearScreen() { entries.innerHTML = ""; }

    // ---------- Terminal input ----------
    function autoGrow() {
      input.style.height = "auto";
      input.style.height = input.scrollHeight + "px";
    }

    function readLine(label, menuId) {
      return new Promise(function (resolve) {
        pendingLabel = label;
        promptEl.textContent = "";
        promptEl.appendChild(make("span", "mint", "❯ "));
        promptEl.appendChild(make("span", "muted", label));
        row.hidden = false;
        input.value = "";
        autoGrow();
        currentMenu = menuId || null;
        historyIndex = history.length;
        resolver = resolve;
        input.focus();
        reveal(row);
      });
    }

    function submit(value) {
      if (!resolver) { return; }
      var done = resolver;
      resolver = null;
      currentMenu = null;
      addEntry(makeLine([["❯ ", "mint"], [pendingLabel, "muted"], [value, "white"]]));
      if (value.trim()) { history.push(value); }
      row.hidden = true;
      done(value);
    }

    input.addEventListener("input", autoGrow);

    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
        e.preventDefault();
        submit(input.value.replace(/\n/g, " "));
      } else if (e.key === "ArrowUp" && input.value.indexOf("\n") === -1) {
        e.preventDefault();
        if (historyIndex > 0) { historyIndex -= 1; input.value = history[historyIndex]; autoGrow(); }
      } else if (e.key === "ArrowDown" && input.value.indexOf("\n") === -1) {
        e.preventDefault();
        if (historyIndex < history.length - 1) { historyIndex += 1; input.value = history[historyIndex]; }
        else { historyIndex = history.length; input.value = ""; }
        autoGrow();
      }
    });

    document.addEventListener("keydown", function (e) {
      if (e.ctrlKey && (e.key === "l" || e.key === "L")) {
        e.preventDefault();
        clearScreen();
      }
    });

    term.addEventListener("click", function () {
      if (!window.getSelection().toString() && resolver) { input.focus(); }
    });

    document.getElementById("clear").addEventListener("click", function () {
      clearScreen();
      if (resolver) { input.focus(); }
    });

    function optionLine(text, note, value, menuId) {
      var parts = [[text, "white"]];
      if (note) { parts.push([" - " + note, "muted"]); }
      var line = makeLine(parts);
      line.classList.add("opt");
      line.addEventListener("click", function () {
        if (resolver && currentMenu === menuId) { submit(value); }
      });
      return line;
    }

    // ---------- Server calls ----------
    async function postJson(url, body) {
      try {
        var res = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body)
        });
        var data = await res.json().catch(function () { return {}; });
        if (!res.ok) {
          return { error: data.error || "The server returned an error (status " + res.status + ")." };
        }
        return data;
      } catch (err) {
        return { error: "Could not reach the server. Please check your internet connection." };
      }
    }

    // ---------- Result ticket ----------
    function renderResult(ticket, provider, model, seconds, text) {
      var steps = parseSteps(text);
      var art = make("article", "ticket");

      var head = make("div", "ticket-head");
      var left = make("div");
      left.appendChild(make("p", "ticket-id", ticket.id));
      left.appendChild(make("h3", "", ticket.title));
      head.appendChild(left);
      head.appendChild(make("p", "ticket-by", "Suggested by " + provider.short + " (" + model + "), " + seconds + "s"));
      art.appendChild(head);

      art.appendChild(make("div", "tear"));

      var list = make("ul", "steps");
      steps.forEach(function (step) {
        var li = make("li");
        var label = make("label", "step");
        var box = make("input");
        box.type = "checkbox";
        label.appendChild(box);
        var visual = make("span", "box");
        visual.setAttribute("aria-hidden", "true");
        label.appendChild(visual);
        label.appendChild(make("span", "text", step));
        li.appendChild(label);
        list.appendChild(li);
      });
      art.appendChild(list);

      var foot = make("div", "ticket-foot");
      var copy = make("button", "copy", "Copy steps");
      copy.type = "button";
      copy.addEventListener("click", function () {
        var plain = steps.map(function (s, i) { return (i + 1) + ". " + s; }).join("\n");
        navigator.clipboard.writeText(plain).then(function () {
          copy.textContent = "Copied";
        }).catch(function () {
          copy.textContent = "Copy failed";
        }).then(function () {
          setTimeout(function () { copy.textContent = "Copy steps"; }, 1600);
        });
      });
      foot.appendChild(copy);
      art.appendChild(foot);
      return art;
    }

    // ---------- Ask the AI ----------
    async function runSuggest(ticket, provider, index) {
      var model = provider.models[index][0];
      var label = provider.name + " / " + model;
      var base = "Getting AI suggestions from " + label + "...";
      var line = addEntry(makeLine([[FRAMES.charAt(0) + " " + base, "yellow"]]));
      var started = Date.now();
      var frame = 0;
      var timer = setInterval(function () {
        frame += 1;
        var secs = ((Date.now() - started) / 1000).toFixed(1);
        line.firstChild.textContent = FRAMES.charAt(frame % FRAMES.length) + " " + base + " " + secs + "s";
      }, 100);

      var result = await postJson("/api/suggest", {
        ticket_id: ticket.id,
        provider: provider.key,
        model_index: index
      });

      clearInterval(timer);
      var seconds = ((Date.now() - started) / 1000).toFixed(1);

      if (result.error) {
        var failed = errorEntry(result.error, true);
        line.replaceWith(failed);
        reveal(failed);
      } else {
        var done = makeLine([["✔ Got AI suggestions", "bgreen"], [" in " + seconds + "s", "muted"]]);
        line.replaceWith(done);
        addEntry(renderResult(ticket, provider, model, seconds, result.suggestions));
      }
    }

    // ---------- Menus ----------
    async function chooseAi() {
      var providerMenu = "m" + (++menuCount);
      addEntry(makeLine([["Choose an AI assistant:", "blue"]]));
      DATA.forEach(function (p) {
        addEntry(optionLine(p.key + ". " + p.name, "", p.key, providerMenu));
      });
      addEntry(optionLine("0. Skip AI suggestions", "", "0", providerMenu));

      var provider = null;
      while (!provider) {
        var c = (await readLine("assistant (0-" + DATA.length + ", Enter for 1): ", providerMenu)).trim() || "1";
        if (c === "0") { return null; }
        provider = DATA.find(function (p) { return p.key === c; }) || null;
        if (!provider) {
          addEntry(makeLine([["Invalid choice. Please enter a number from 0 to " + DATA.length + ".", "red"]]));
        }
      }

      var modelMenu = "m" + (++menuCount);
      addEntry(makeLine([["Choose a " + provider.name + " model:", "blue"]]));
      provider.models.forEach(function (m, i) {
        addEntry(optionLine((i + 1) + ". " + m[0], m[1], String(i + 1), modelMenu));
      });

      var n = provider.models.length;
      while (true) {
        var m = (await readLine("model (1-" + n + ", Enter for 1): ", modelMenu)).trim() || "1";
        var idx = parseInt(m, 10);
        if (/^\d+$/.test(m) && idx >= 1 && idx <= n) {
          return { provider: provider, index: idx - 1 };
        }
        addEntry(makeLine([["Invalid choice. Please enter a number from 1 to " + n + ".", "red"]]));
      }
    }

    async function askNonEmpty(label, message) {
      while (true) {
        var value = (await readLine(label)).trim();
        if (value) { return value; }
        addEntry(makeLine([[message, "red"]]));
      }
    }

    // ---------- One ticket, start to finish ----------
    async function ticketSession() {
      var title = await askNonEmpty("title: ", "The title cannot be empty.");
      var description = await askNonEmpty("describe: ", "The description cannot be empty.");

      var saved = await postJson("/api/ticket", { title: title, description: description });
      if (saved.error) {
        addEntry(errorEntry("The ticket could not be saved: " + saved.error, false));
        return;
      }

      var ticket = saved.ticket;
      addEntry(makeLine([["✔ Ticket " + ticket.id + " saved. ", "bgreen"], [ticket.title, "muted"]]));

      while (true) {
        var choice = await chooseAi();
        if (choice === null) {
          addEntry(makeLine([["Skipped AI suggestions. Your ticket is saved.", "muted"]]));
          return;
        }

        await runSuggest(ticket, choice.provider, choice.index);

        var again = (await readLine("try another assistant on this ticket? (y/n): ")).trim().toLowerCase();
        if (again !== "y") { return; }
      }
    }

    async function main() {
      addEntry(makeLine([["Type an answer and press Enter. ↑ ↓ recall earlier answers, Ctrl + L clears the screen.", "muted"]]));
      while (true) {
        await ticketSession();
        addEntry(make("div", "spacer"));
      }
    }

    main();
  })();
  </script>
  {% endraw %}
</body>
</html>
"""


def short_name(provider):
    return provider["name"].split(" (")[0]


def pick_tickets_file():
    # Use main.py's tickets file if its folder is writable (your laptop).
    # Otherwise use /tmp (hosting servers with a read-only app folder).
    folder = os.path.dirname(os.path.abspath(FILE))
    if os.access(folder, os.W_OK):
        return FILE
    return os.path.join(tempfile.gettempdir(), "tickets.json")


TICKETS_FILE = pick_tickets_file()


def load_tickets():
    if os.path.exists(TICKETS_FILE):
        with open(TICKETS_FILE, "r") as f:
            return json.load(f)
    return []


def save_ticket(title, description):
    tickets = load_tickets()
    ticket = {
        "id": f"A{len(tickets) + 1:03d}",
        "title": title,
        "description": description,
    }
    tickets.append(ticket)
    with open(TICKETS_FILE, "w") as f:
        json.dump(tickets, f, indent=4)
    return ticket


@app.route("/")
def home():
    data = {
        "providers": [
            {
                "key": key,
                "name": provider["name"],
                "short": short_name(provider),
                "models": [[name, note] for name, note in provider["models"]],
            }
            for key, provider in PROVIDERS.items()
        ]
    }
    return render_template_string(PAGE, data=data)


@app.post("/api/ticket")
def api_ticket():
    body = request.get_json(silent=True) or {}
    title = str(body.get("title", "")).strip()
    description = str(body.get("description", "")).strip()

    if not title or not description:
        return jsonify(error="Title and description cannot be empty."), 400

    try:
        ticket = save_ticket(title, description)
    except (OSError, json.JSONDecodeError) as e:
        return jsonify(error=str(e)), 500

    return jsonify(ticket=ticket)


@app.post("/api/suggest")
def api_suggest():
    body = request.get_json(silent=True) or {}
    ticket_id = str(body.get("ticket_id", ""))

    try:
        provider = PROVIDERS[str(body.get("provider", ""))]
        model_index = int(body.get("model_index", -1))
        if model_index < 0:
            raise IndexError
        model = provider["models"][model_index][0]
    except (KeyError, ValueError, IndexError, TypeError):
        return jsonify(error="Unknown AI provider or model."), 400

    try:
        ticket = next((t for t in load_tickets() if t["id"] == ticket_id), None)
    except (OSError, json.JSONDecodeError) as e:
        return jsonify(error=f"Could not read the saved tickets: {e}"), 500

    if ticket is None:
        return jsonify(error="That ticket was not found."), 404

    suggestions, error = get_ai_suggestions(ticket, provider, model)
    if error:
        return jsonify(error=error), 502

    return jsonify(suggestions=suggestions)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))