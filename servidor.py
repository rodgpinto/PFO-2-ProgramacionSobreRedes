"""PFO 2 - API REST con Flask + SQLite.
Endpoints: POST /registro, POST /login, GET /tareas
"""
import os
import sqlite3

from flask import Flask, g, jsonify, render_template_string, request, session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
# En producción definir SECRET_KEY como variable de entorno.
app.secret_key = os.environ.get("SECRET_KEY", "clave-de-desarrollo-cambiar")

# Ruta de la base: configurable (en Render con disco persistente: /var/data/usuarios.db)
DB_PATH = os.environ.get(
    "DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "usuarios.db")
)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def cerrar_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS usuarios (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   usuario TEXT NOT NULL UNIQUE,
                   password_hash TEXT NOT NULL
               )"""
        )


PAGINA_PRUEBA = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PFO 2 - Probar API</title>
<style>
 body{font-family:sans-serif;max-width:560px;margin:2rem auto;padding:0 1rem}
 input,button{padding:.5rem;margin:.2rem 0;width:100%;box-sizing:border-box}
 pre{background:#eee;padding:1rem;white-space:pre-wrap}
</style></head><body>
<h1>Probar la API</h1>
<input id="u" placeholder="usuario">
<input id="p" type="password" placeholder="contraseña">
<button onclick="enviar('/registro')">POST /registro</button>
<button onclick="enviar('/login')">POST /login</button>
<button onclick="ver()">GET /tareas</button>
<button onclick="salir()">POST /logout</button>
<h3>Respuesta</h3><pre id="out">-</pre>
<h3>Vista de /tareas</h3>
<iframe id="vista" style="width:100%;height:160px;border:1px solid #ccc"></iframe>
<script>
const out = document.getElementById('out');
async function enviar(ruta){
  const r = await fetch(ruta,{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({usuario:u.value,"contraseña":p.value})});
  out.textContent = r.status + ' ' + await r.text();
}
async function ver(){
  const r = await fetch('/tareas');
  const t = await r.text();
  out.textContent = r.status + (r.ok ? ' (HTML renderizado abajo)' : ' ' + t);
  document.getElementById('vista').srcdoc = r.ok ? t : '';
}
async function salir(){
  const r = await fetch('/logout',{method:'POST'});
  out.textContent = r.status + ' ' + await r.text();
  document.getElementById('vista').srcdoc = '';
}
</script></body></html>"""


@app.route("/", methods=["GET"])
def inicio():
    return PAGINA_PRUEBA


@app.route("/registro", methods=["POST"])
def registro():
    datos = request.get_json(silent=True) or {}
    usuario = str(datos.get("usuario", "")).strip()
    contraseña = str(datos.get("contraseña", ""))

    if not usuario or not contraseña:
        return jsonify({"error": "Faltan 'usuario' o 'contraseña'"}), 400

    try:
        db = get_db()
        db.execute(
            "INSERT INTO usuarios (usuario, password_hash) VALUES (?, ?)",
            (usuario, generate_password_hash(contraseña)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "El usuario ya existe"}), 409

    return jsonify({"mensaje": f"Usuario '{usuario}' registrado correctamente"}), 201


@app.route("/login", methods=["POST"])
def login():
    datos = request.get_json(silent=True) or {}
    usuario = str(datos.get("usuario", "")).strip()
    contraseña = str(datos.get("contraseña", ""))

    fila = get_db().execute(
        "SELECT * FROM usuarios WHERE usuario = ?", (usuario,)
    ).fetchone()

    if fila is None or not check_password_hash(fila["password_hash"], contraseña):
        return jsonify({"error": "Credenciales inválidas"}), 401

    session["usuario"] = fila["usuario"]
    return jsonify({"mensaje": f"Bienvenido, {usuario}"}), 200


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"mensaje": "Sesión cerrada"}), 200


PLANTILLA = """<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><title>Tareas</title></head>
<body style="font-family: sans-serif; text-align: center; margin-top: 4rem;">
  <h1>¡Bienvenido, {{ usuario }}!</h1>
  <p>Has iniciado sesión correctamente. Este es tu gestor de tareas.</p>
</body>
</html>"""


@app.route("/tareas", methods=["GET"])
def tareas():
    usuario = session.get("usuario")
    if not usuario:
        return jsonify({"error": "Debes iniciar sesión en /login"}), 401
    return render_template_string(PLANTILLA, usuario=usuario)


# Se ejecuta también al arrancar con gunicorn (Render)
init_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000)