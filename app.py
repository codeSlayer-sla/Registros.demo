import identity
import identity.web
import uuid
import requests
from flask import Flask, redirect, render_template, request, session, url_for,jsonify
from flask_session import Session
import sqlite3
import app_config
from datetime import datetime
conn=sqlite3.connect("Registros_cronometros")
cursor=conn.cursor()
# Crear la tabla solo si no existe
# cursor.execute("""
#     CREATE TABLE IF NOT EXISTS Tareas (
#         id_tarea text PRIMARY KEY,
#         id_timer TEXT,      
#         Usuario TEXT,
#         Cliente TEXT,
#         Software TEXT,                     
#         Creacion TEXT,                  
#         Tiempo_transcurrido TEXT,       
#         Finalizacion TEXT,
#         Razon TEXT,              
#         Estado TEXT                  
#     )
# """)
#Verificar la estructura de la tabla 'cronometros'
cursor.execute("PRAGMA table_info(Tareas);")
columns = cursor.fetchall()
print("\nEstructura de la tabla 'Tareas':")
for column in columns:
       print(column)
# #Verificar que el dato se haya insertado correctamente
cursor.execute("SELECT * FROM Tareas")
result = cursor.fetchall()  # Obtener el registro insertado

#Imprimir los datos guardados para verificar
print(f"Datos guardados en la base de datos: {result}")  # Esto imprime los datos de la fila insertada

conn.close()

# Confirmar los cambios y cerrar la conexión
# conn.commit()
# conn.close()
####################################################################################################################################
app = Flask(__name__)
app.config.from_object(app_config)
Session(app)
# Simulando listas de clientes y softwares
clientes = ['Cliente 1', 'Cliente 2', 'Cliente 3']
softwares = ['Software A', 'Software B', 'Software C']
tareas=["soporteMIBUS","InvestigacionMIVIOT"]

# This section is needed for url_for("foo", _external=True) to automatically
# generate http scheme when this sample is running on localhost,
# and to generate https scheme when it is deployed behind reversed proxy.
# See also https://flask.palletsprojects.com/en/2.2.x/deploying/proxy_fix/
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

auth = identity.web.Auth(
    session=session,
    authority=app.config.get("AUTHORITY"),
    client_id=app.config["CLIENT_ID"],
    client_credential=app.config["CLIENT_SECRET"],
)
# Conexión a la base de datos SQLite
def get_db_connection():
    conn = sqlite3.connect('Registros_cronometros')
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/login")
def login():
    return render_template("login.html", version=identity.__version__, **auth.log_in(
        scopes=app_config.SCOPE, # Have user consent to scopes during log-in
        redirect_uri=url_for("auth_response", _external=True), # Optional. If present, this absolute URL must match your app's redirect_uri registered in Azure Portal
        ))


@app.route(app_config.REDIRECT_PATH)
def auth_response():
    result = auth.complete_log_in(request.args)
    if "error" in result:
        return render_template("auth_error.html", result=result)
    user_info = auth.get_user()
    session["user"] = {
        "name": user_info.get("name"),
        "email": user_info.get("preferred_username"),
        "id": user_info.get("oid"),
    }
    print(user_info.get("preferred_username"))

    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    return redirect(auth.log_out(url_for("index", _external=True)))

@app.route("/timer")
def timer():
    if 'id_timer'  not in session:
        # Si no existe, mostrar el modal en el frontend
        return render_template('timer.html', clientes=clientes, softwares=softwares,tareas=tareas,modal=True)
    else:
        return render_template('timer.html',modal=False, clientes=clientes,tareas=tareas,softwares=softwares)

@app.route("/")
def index():
    cronometros = session.get("registros_cronometros", [])
    if not (app.config["CLIENT_ID"] and app.config["CLIENT_SECRET"]):
        # This check is not strictly necessary.
        # You can remove this check from your production code.
        return render_template('config_error.html')
    if not auth.get_user():
        return redirect(url_for("login"))
    return render_template('registros.html', user=auth.get_user(), version=identity.__version__,cronometros=cronometros)

@app.route("/guardar_registro", methods=["POST"])
def guardar_registro():
    # Obtener el tiempo y estado desde el formulario
    tiempo = int(request.form["tiempo"])
    estado = request.form["estado"]
    # Crear un id único para este registro usando uuid
    id_timer = request.form["IDTime"]  # Genera un id único basado en UUID
    
    # Crear un nuevo registro
    from datetime import datetime
    registro = {
        "id": id_timer,# Genera un id único basado en UUID
        "tiempo": tiempo,
        "ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "estado": estado
    }
    
    # Guardar el registro en la sesión (o en la base de datos)
    if "registros_cronometros" not in session:
        session["registros_cronometros"] = []
    
    session["registros_cronometros"].append(registro)
    session.modified = True  # Asegurarse de que la sesión se actualice

    # Redirigir a la página de registros
    return redirect(url_for("timer"))

@app.route("/ver_registros")
def ver_registros():
    cronometros = session.get("registros_cronometros", [])
    return render_template("registros.html", cronometros=cronometros)

@app.route('/Crear_Id', methods=['POST'])
def crear_id():
    data = request.get_json()  # Obtener los datos JSON de la solicitud
    print(f"Datos recibidos: {data}")  # Imprimir los datos recibidos para depuración
    
    # Generar un nuevo id_timer (UUID)
    id_timer = str(uuid.uuid4())  # Genera un ID único
    id_tarea = str(uuid.uuid4())  # Genera un ID único para la tarea
    Usuario = request.json.get("username")
    cliente = request.json.get('cliente')
    software = request.json.get('software')
    Descripcion=request.json.get("Descripcion")

    # Crear una fecha de creación
    creacion = datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    # Insertar los datos en la tabla
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Tareas (id_tarea,id_timer,Descripcion,Usuario, Cliente, Software, Creacion, Estado)
        VALUES (?, ? , ?, ?, ?, ?, ? , ? )
    """, (id_tarea,id_timer,Descripcion,Usuario, cliente, software, creacion, 'Activo'))
    conn.commit()
    conn.close()

    # Devolver el id_timer creado al frontend
    return jsonify({'id_timer': id_timer}), 200

@app.route("/check_id_timer", methods=["GET"])
def check_id_timer():
     # Verificar si el id_timer existe en la sesión
     id_timer = session.get("id_timer")
     if id_timer:
         # Si existe, devolver el id_timer
         return jsonify({"id_timer": id_timer})
     else:
         # Si no existe, devolver un objeto vacío
         return jsonify({"id_timer": None})


@app.route("/cambiar_modal", methods=["POST"])
def cambiar_modal():

    session["modal"] = True  # Establecer 'modal' a True en la sesión
    session.modified = True   # Asegurarse de que la sesión se actualice
    return render_template('timer.html',modal=True)


if __name__ == "__main__":
    app.run(host='localhost', port=5050, debug=True)
