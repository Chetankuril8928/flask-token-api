from flask import Flask, request, jsonify, render_template_string
import uuid, hashlib, datetime

app = Flask(__name__)

# ── In-memory storage ─────────────────────────────────────────────────────────
users = {}   # { user_id: {id, username, password_hash} }
tokens = {}  # { token: user_id }
items = {}   # { item_id: {id, name, description, owner_id} }

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def now():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

def get_user_from_token():
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not token or token not in tokens:
        return None, None
    user_id = tokens[token]
    return user_id, token

# ── HTML PAGE ─────────────────────────────────────────────────────────────────
PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Flask REST API — Token Auth</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Segoe UI',sans-serif;background:#0f172a;color:#e2e8f0;padding:20px}
  h1{color:#60a5fa;text-align:center;font-size:2.2rem;padding:20px 0 5px}
  .subtitle{text-align:center;color:#94a3b8;margin-bottom:25px}
  .token-bar{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:14px 18px;max-width:900px;margin:0 auto 30px;display:flex;align-items:center;gap:10px}
  .token-bar b{color:#fbbf24;white-space:nowrap}
  #tok{flex:1;color:#34d399;font-size:.82rem;word-break:break-all;font-family:monospace}
  .copy-btn{background:#334155;color:#e2e8f0;border:none;padding:7px 14px;border-radius:6px;cursor:pointer;white-space:nowrap}
  .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:18px;max-width:1200px;margin:0 auto}
  .card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:20px}
  .card-title{display:flex;align-items:center;gap:8px;margin-bottom:14px}
  .card-title h3{font-size:.95rem;color:#e2e8f0}
  .badge{padding:3px 9px;border-radius:4px;font-size:.72rem;font-weight:700}
  .POST{background:#065f46;color:#34d399}
  .GET{background:#1e3a5f;color:#60a5fa}
  .DELETE{background:#7f1d1d;color:#f87171}
  input,textarea{width:100%;padding:9px 12px;background:#0f172a;border:1px solid #334155;border-radius:7px;color:#e2e8f0;margin-bottom:9px;font-size:.88rem;outline:none}
  input:focus,textarea:focus{border-color:#60a5fa}
  .btn{width:100%;padding:10px;background:#3b82f6;color:#fff;border:none;border-radius:7px;cursor:pointer;font-weight:600;font-size:.9rem;transition:background .2s}
  .btn:hover{background:#2563eb}
  .btn.red{background:#dc2626}.btn.red:hover{background:#b91c1c}
  .res{margin-top:12px;padding:12px;background:#0f172a;border-radius:7px;font-size:.78rem;min-height:44px;white-space:pre-wrap;word-break:break-all;font-family:monospace;border-left:3px solid #334155}
  .ok{border-left-color:#34d399;color:#34d399}
  .err{border-left-color:#f87171;color:#f87171}
  .section-title{max-width:1200px;margin:25px auto 12px;color:#64748b;font-size:.75rem;letter-spacing:2px;text-transform:uppercase}
</style>
</head>
<body>
<h1>🔥 Flask REST API</h1>
<p class="subtitle">Token Authentication + CRUD — College Project Demo</p>

<div class="token-bar">
  <b>🔑 TOKEN:</b>
  <div id="tok">No token yet — register then login below</div>
  <button class="copy-btn" onclick="navigator.clipboard.writeText(document.getElementById('tok').innerText)">Copy</button>
</div>

<p class="section-title">── Auth Endpoints ──────────────────────────────</p>
<div class="grid">

  <div class="card">
    <div class="card-title"><span class="badge POST">POST</span><h3>/register — Create Account</h3></div>
    <input id="ru" placeholder="Username" value="chetan">
    <input id="rp" placeholder="Password" type="password" value="1234">
    <button class="btn" onclick="reg()">Register →</button>
    <div class="res" id="rr">Response will appear here...</div>
  </div>

  <div class="card">
    <div class="card-title"><span class="badge POST">POST</span><h3>/login — Get Token</h3></div>
    <input id="lu" placeholder="Username" value="chetan">
    <input id="lp" placeholder="Password" type="password" value="1234">
    <button class="btn" onclick="login()">Login →</button>
    <div class="res" id="lr">Response will appear here...</div>
  </div>

  <div class="card">
    <div class="card-title"><span class="badge POST">POST</span><h3>/logout — Invalidate Token</h3></div>
    <p style="color:#94a3b8;font-size:.85rem;margin-bottom:12px">Uses token from login automatically</p>
    <button class="btn red" onclick="logout()">Logout →</button>
    <div class="res" id=" lor">Response will appear here...</div>
  </div>

</div>

<p class="section-title">── Protected Endpoints (need token) ────────────</p>
<div class="grid">

  <div class="card">
    <div class="card-title"><span class="badge GET">GET</span><h3>/users — List All Users</h3></div>
    <button class="btn" onclick="getUsers()">Get Users →</button>
    <div class="res" id="ur">Response will appear here...</div>
  </div>

  <div class="card">
    <div class="card-title"><span class="badge GET">GET</span><h3>/items — List All Items</h3></div>
    <button class="btn" onclick="getItems()">Get Items →</button>
    <div class="res" id="ir">Response will appear here...</div>
  </div>

  <div class="card">
    <div class="card-title"><span class="badge POST">POST</span><h3>/items — Create Item</h3></div>
    <input id="iname" placeholder="Item name" value="laptop">
    <input id="idesc" placeholder="Description" value="my laptop">
    <button class="btn" onclick="createItem()">Create Item →</button>
    <div class="res" id="icr">Response will appear here...</div>
  </div>

  <div class="card">
    <div class="card-title"><span class="badge DELETE">DELETE</span><h3>/items/:id — Delete Item</h3></div>
    <input id="delid" placeholder="Paste item ID here">
    <button class="btn red" onclick="deleteItem()">Delete Item →</button>
    <div class="res" id="dr">Response will appear here...</div>
  </div>

</div>

<script>
let TOKEN = '';
const BASE = window.location.origin;

function show(id, data, ok) {
  const el = document.getElementById(id);
  el.textContent = JSON.stringify(data, null, 2);
  el.className = 'res ' + (ok ? 'ok' : 'err');
}

async function call(method, path, body, id) {
  try {
    const opts = {
      method,
      headers: { 'Content-Type': 'application/json', ...(TOKEN ? { Authorization: 'Bearer ' + TOKEN } : {}) },
      ...(body ? { body: JSON.stringify(body) } : {})
    };
    const r = await fetch(BASE + path, opts);
    const data = await r.json();
    show(id, data, r.ok);
    return { ok: r.ok, data };
  } catch(e) {
    show(id, { error: 'Network error: ' + e.message }, false);
  }
}

async function reg() {
  await call('POST', '/register', { username: document.getElementById('ru').value, password: document.getElementById('rp').value }, 'rr');
}

async function login() {
  const res = await call('POST', '/login', { username: document.getElementById('lu').value, password: document.getElementById('lp').value }, 'lr');
  if (res && res.ok && res.data.token) {
    TOKEN = res.data.token;
    document.getElementById('tok').textContent = TOKEN;
  }
}

async function logout() {
  await call('POST', '/logout', null, 'lor');
  TOKEN = '';
  document.getElementById('tok').textContent = 'Logged out — login again';
}

async function getUsers()  { await call('GET', '/users', null, 'ur'); }
async function getItems()  { await call('GET', '/items', null, 'ir'); }

async function createItem() {
  const res = await call('POST', '/items', { name: document.getElementById('iname').value, description: document.getElementById('idesc').value }, 'icr');
  if (res && res.ok && res.data.item) {
    document.getElementById('delid').value = res.data.item.id;
  }
}

async function deleteItem() {
  const id = document.getElementById('delid').value.trim();
  await call('DELETE', '/items/' + id, null, 'dr');
}
</script>
</body>
</html>"""

@app.route("/")
def index():
    return render_template_string(PAGE)

# ── AUTH ──────────────────────────────────────────────────────────────────────
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data or not data.get("username") or not data.get("password"):
        return jsonify({"error": "username and password required"}), 400
    username = data["username"].strip()
    if any(u["username"] == username for u in users.values()):
        return jsonify({"error": "Username already exists"}), 409
    uid = str(uuid.uuid4())
    users[uid] = {"id": uid, "username": username, "password_hash": hash_pw(data["password"]), "created_at": now()}
    return jsonify({"message": "Registered successfully!", "user_id": uid}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "username and password required"}), 400
    user = next((u for u in users.values() if u["username"] == data.get("username", "")), None)
    if not user or user["password_hash"] != hash_pw(data.get("password", "")):
        return jsonify({"error": "Invalid credentials"}), 401
    # Remove old token
    old = next((t for t, uid in tokens.items() if uid == user["id"]), None)
    if old: del tokens[old]
    token = str(uuid.uuid4()).replace("-", "")
    tokens[token] = user["id"]
    return jsonify({"message": "Login successful!", "token": token})

@app.route("/logout", methods=["POST"])
def logout():
    user_id, token = get_user_from_token()
    if not token:
        return jsonify({"error": "No token provided"}), 401
    del tokens[token]
    return jsonify({"message": "Logged out successfully!"})

# ── USERS ─────────────────────────────────────────────────────────────────────
@app.route("/users", methods=["GET"])
def get_users():
    user_id, _ = get_user_from_token()
    if not user_id:
        return jsonify({"error": "Token required"}), 401
    return jsonify({"users": [{"id": u["id"], "username": u["username"]} for u in users.values()]})

# ── ITEMS ─────────────────────────────────────────────────────────────────────
@app.route("/items", methods=["GET"])
def get_items():
    user_id, _ = get_user_from_token()
    if not user_id:
        return jsonify({"error": "Token required"}), 401
    return jsonify({"items": list(items.values())})

@app.route("/items", methods=["POST"])
def create_item():
    user_id, _ = get_user_from_token()
    if not user_id:
        return jsonify({"error": "Token required"}), 401
    data = request.get_json()
    if not data or not data.get("name"):
        return jsonify({"error": "name is required"}), 400
    iid = str(uuid.uuid4())
    item = {"id": iid, "name": data["name"], "description": data.get("description", ""), "owner_id": user_id, "created_at": now()}
    items[iid] = item
    return jsonify({"message": "Item created!", "item": item}), 201

@app.route("/items/<item_id>", methods=["DELETE"])
def delete_item(item_id):
    user_id, _ = get_user_from_token()
    if not user_id:
        return jsonify({"error": "Token required"}), 401
    item = items.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    if item["owner_id"] != user_id:
        return jsonify({"error": "You can only delete your own items"}), 403
    del items[item_id]
    return jsonify({"message": "Item deleted!"})

if __name__ == "__main__":
    app.run(debug=True)
