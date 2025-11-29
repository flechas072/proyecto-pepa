from flask import Flask, render_template, request, redirect, url_for, session, flash
from pepa import conectar, validar_usuario, mostrar_estudiantes, insertar_estudiante

import mysql.connector

def obtener_conexion():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="pila245A*",
        database="pepa"
    )

app = Flask(__name__)
app.secret_key = "clave_secreta_segura"

# ----------------- LOGIN -----------------

@app.route("/", methods=["GET", "POST"])
def login_view():
    if request.method == "POST":
        user = request.form.get("usuario")
        pwd = request.form.get("contrasena")

        conexion = conectar()
        if not conexion or not conexion.is_connected():
            flash("Error: No se pudo conectar a la base de datos", "error")
            return render_template("login.html")

        usuario = validar_usuario(conexion, user, pwd)
        conexion.close()

        if usuario:
            session["usuario"] = usuario[1]
            session["id_usuario"] = usuario[0]
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Usuario o contraseña incorrectos")

    return render_template("login.html")

@app.route("/usuario/crear", methods=["GET", "POST"])
def crear_usuario():
    if request.method == "POST":
        nombre_usuario = request.form["nombre_usuario"]
        contrasena = request.form["contrasena"]
        nombre_completo = request.form.get("nombre_completo")
        email = request.form.get("email")

        conexion = obtener_conexion()
        cursor = conexion.cursor()

        try:
            cursor.execute(
                "INSERT INTO usuario (nombre_usuario, contrasena, nombre_completo, email) VALUES (%s, %s, %s, %s)",
                (nombre_usuario, contrasena, nombre_completo, email)
            )
            conexion.commit()

            return redirect(url_for("login_view"))

        except mysql.connector.IntegrityError:
            # Aquí capturas cuando el usuario ya existe
            error = "⚠️ Ese nombre de usuario ya está registrado, intenta con otro."
            return render_template("crear_usuario.html", error=error)

        finally:
            cursor.close()
            conexion.close()

    return render_template("crear_usuario.html")



# ----------------- DASHBOARD -----------------

@app.route("/dashboard")
def dashboard():
    if "usuario" not in session:
        return redirect(url_for("login_view"))
    return render_template("dashboard.html", usuario=session["usuario"])

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_view"))

# ----------------- RUTAS PARA ESTUDIANTES -----------------

@app.route("/estudiantes")
def estudiantes_list():
    if "usuario" not in session:
        return redirect(url_for("login_view"))

    conexion = conectar()
    if not conexion or not conexion.is_connected():
        flash("Error al conectar a la base de datos", "error")
        return render_template("estudiantes.html", estudiantes=[])

    estudiantes = mostrar_estudiantes(conexion) or []
    conexion.close()

    return render_template("estudiantes.html", estudiantes=estudiantes, usuario=session["usuario"])

@app.route("/estudiantes/nuevo", methods=["GET", "POST"])
def estudiantes_nuevo():
    if "usuario" not in session:
        return redirect(url_for("login_view"))

    conexion = conectar()
    if not conexion or not conexion.is_connected():
        flash("Error al conectar a la base de datos", "error")
        return redirect(url_for("estudiantes_list"))

    cursor = conexion.cursor()
    cursor.execute("SELECT id_programa, nombre_programa FROM programa ORDER BY id_programa")
    programas = cursor.fetchall()
    cursor.close()

    if request.method == "POST":
        nombre = request.form.get("nombre")
        apellido = request.form.get("apellido")
        cedula = request.form.get("cedula")
        telefono = request.form.get("telefono")
        email = request.form.get("email")
        id_programa = request.form.get("id_programa")

        if not id_programa:
            flash("Debe seleccionar un programa", "error")
        else:
            try:
                insertar_estudiante(conexion, nombre, apellido, cedula, telefono, email, int(id_programa))
                flash("Estudiante creado correctamente", "success")
                conexion.close()
                return redirect(url_for("estudiantes_list"))
            except Exception as e:
                flash(f"Error al insertar estudiante: {e}", "error")

    conexion.close()
    return render_template("estudiante_form.html", modos="nuevo", programas=programas, estudiante=None, usuario=session["usuario"])

@app.route("/estudiantes/editar/<int:id_estudiante>", methods=["GET", "POST"])
def estudiantes_editar(id_estudiante):
    if "usuario" not in session:
        return redirect(url_for("login_view"))

    conexion = conectar()
    if not conexion or not conexion.is_connected():
        flash("Error: No hay conexión a base de datos", "error")
        return redirect(url_for("estudiantes_list"))

    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM estudiante WHERE id_estudiante = %s", (id_estudiante,))
    estudiante = cursor.fetchone()
    cursor.close()

    # Cargar programas para el select
    cursor = conexion.cursor()
    cursor.execute("SELECT id_programa, nombre_programa FROM programa ORDER BY id_programa")
    programas = cursor.fetchall()
    cursor.close()

    if request.method == "POST":
        nombre = request.form.get("nombre")
        apellido = request.form.get("apellido")
        cedula = request.form.get("cedula")
        telefono = request.form.get("telefono")
        email = request.form.get("email")
        id_programa = request.form.get("id_programa")

        try:
            cursor = conexion.cursor()
            cursor.execute("""
                UPDATE estudiante 
                SET nombre=%s, apellido=%s, cedula=%s, telefono=%s, email=%s, id_programa=%s
                WHERE id_estudiante=%s
            """, (nombre, apellido, cedula, telefono, email, int(id_programa), id_estudiante))

            conexion.commit()
            cursor.close()
            conexion.close()
            flash("Estudiante actualizado", "success")
            return redirect(url_for("estudiantes_list"))

        except Exception as e:
            flash(f"Error al actualizar: {e}", "error")

    conexion.close()
    return render_template(
        "estudiante_form.html",
        modos="editar",
        programas=programas,
        estudiante=estudiante,
        usuario=session["usuario"]
    )

@app.route("/estudiantes/eliminar/<int:id_estudiante>", methods=["POST"])
def estudiantes_eliminar(id_estudiante):
    if "usuario" not in session:
        return redirect(url_for("login_view"))

    conexion = conectar()
    if not conexion or not conexion.is_connected():
        flash("Error: No hay conexión a base de datos", "error")
        return redirect(url_for("estudiantes_list"))

    try:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM estudiante WHERE id_estudiante = %s", (id_estudiante,))
        conexion.commit()
        cursor.close()
        flash("Estudiante eliminado correctamente", "success")
    except Exception as e:
        flash(f"Error al eliminar estudiante: {e}", "error")

    conexion.close()
    return redirect(url_for("estudiantes_list"))

# ----------------------------------------------------------

# Rutas placeholder para evitar 404 mientras creas esos HTML luego
@app.route("/programas")
def programas_list():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id_programa, nombre_programa FROM programa")
    programas = cursor.fetchall()
    cursor.close()
    conexion.close()

    return render_template("programas.html", usuario=session.get("usuario"), programas=programas)

@app.route("/asignaturas")
def asignaturas_list():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id_asignatura, nombre_asignatura FROM asignatura")
    asignaturas = cursor.fetchall()
    cursor.close()
    conexion.close()

    return render_template("asignaturas.html", usuario=session.get("usuario"), asignaturas=asignaturas)

@app.route("/sesiones")
def sesiones_list():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM sesion_asesoria")
    sesiones = cursor.fetchall()
    cursor.close()
    conexion.close()

    return render_template("sesiones.html", usuario=session.get("usuario"), sesiones=sesiones)

# ---------------------------------------------------------

@app.route("/programas/agregar")
def agregar_programa():
    return render_template("agregar_programa.html", usuario=session.get("usuario"))

@app.route("/programas/guardar", methods=["POST"])
def guardar_programa():
    nombre = request.form["nombre"]

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO programa (nombre_programa) VALUES (%s)", (nombre,))
    conexion.commit()
    cursor.close()
    conexion.close()

    return redirect("/programas")

@app.route("/programas/editar/<int:id_programa>")
def editar_programa(id_programa):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id_programa, nombre_programa FROM programa WHERE id_programa = %s", (id_programa,))
    programa = cursor.fetchone()
    cursor.close()
    conexion.close()

    return render_template("editar_programa.html", programa=programa)

@app.route("/programas/actualizar/<int:id_programa>", methods=["POST"])
def actualizar_programa(id_programa):
    nombre = request.form["nombre_programa"]

    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("""
        UPDATE programa 
        SET nombre_programa = %s 
        WHERE id_programa = %s
    """, (nombre, id_programa))
    conexion.commit()
    cursor.close()
    conexion.close()

    return redirect("/programas")

@app.route("/programas/eliminar/<int:id_programa>", methods=["POST"])
def eliminar_programa(id_programa):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM programa WHERE id_programa=%s", (id_programa,))
    conexion.commit()

    cursor.close()
    conexion.close()
    return redirect("/programas")

@app.route("/asignaturas/agregar", methods=["GET", "POST"])
def asignaturas_agregar():
    if "usuario" not in session:
        return redirect(url_for("login_view"))

    if request.method == "POST":
        nombre = request.form.get("nombre")

        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO asignatura (nombre_asignatura) VALUES (%s)", (nombre,))
        conexion.commit()
        cursor.close()
        conexion.close()

        flash("Asignatura agregada correctamente", "success")
        return redirect(url_for("asignaturas_list"))

    return render_template("asignatura_form.html", modo="agregar", usuario=session.get("usuario"))

@app.route("/asignaturas/editar/<int:id_asignatura>", methods=["GET", "POST"])
def asignaturas_editar(id_asignatura):
    if "usuario" not in session:
        return redirect(url_for("login_view"))

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM asignatura WHERE id_asignatura = %s", (id_asignatura,))
    asignatura = cursor.fetchone()
    cursor.close()

    if not asignatura:
        flash("Asignatura no encontrada", "error")
        return redirect(url_for("asignaturas_list"))

    if request.method == "POST":
        nombre = request.form.get("nombre")

        try:
            cursor = conexion.cursor()
            cursor.execute("""
                UPDATE asignatura
                SET nombre_asignatura=%s
                WHERE id_asignatura=%s
            """, (nombre, id_asignatura))
            conexion.commit()
            cursor.close()
            conexion.close()

            flash("Asignatura actualizada correctamente", "success")
            return redirect(url_for("asignaturas_list"))
        except Exception as e:
            flash(f"Error al actualizar: {e}", "error")

    conexion.close()
    return render_template("asignatura_form.html",
                           modo="editar",
                           asignatura=asignatura,
                           usuario=session.get("usuario"))

@app.route('/asignaturas/eliminar/<int:id_asignatura>', methods=["GET"])
def asignaturas_eliminar(id_asignatura):
    if "usuario" not in session:
        return redirect(url_for("login_view"))

    conn = conectar()
    cursor = conn.cursor()

    # Verificar si hay sesiones asociadas
    cursor.execute("SELECT COUNT(*) FROM sesion_asesoria WHERE id_asignatura=%s", (id_asignatura,))
    count = cursor.fetchone()[0]

    if count > 0:
        cursor.close()
        conn.close()
        flash("No se puede eliminar esta asignatura porque tiene sesiones de asesoría asociadas. "
              "Elimina esas sesiones primero.", "error")
        return redirect(url_for("asignaturas_list"))

    try:
        cursor.execute("DELETE FROM asignatura WHERE id_asignatura=%s", (id_asignatura,))
        conn.commit()

        cursor.close()
        conn.close()

        flash("Asignatura eliminada correctamente.", "success")
        return redirect(url_for("asignaturas_list"))

    except Exception as e:
        cursor.close()
        conn.close()
        flash(f"Error al eliminar: {e}", "error")
        return redirect(url_for("asignaturas_list"))

@app.route("/sesiones/agregar", methods=["GET", "POST"])
def sesiones_agregar():
    if "usuario" not in session:
        return redirect(url_for("login_view"))

    if request.method == "POST":
        fecha = request.form.get("fecha")
        hora_inicio = request.form.get("hora_inicio")
        hora_fin = request.form.get("hora_fin")
        tema = request.form.get("tema")
        id_monitor = request.form.get("id_monitor")
        id_estudiante = request.form.get("id_estudiante")
        id_asignatura = request.form.get("id_asignatura")

        conexion = conectar()
        cursor = conexion.cursor()

        cursor.execute("""
            INSERT INTO sesion_asesoria (fecha, hora_inicio, hora_fin, tema, id_monitor, id_estudiante, id_asignatura)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (fecha, hora_inicio, hora_fin, tema, id_monitor, id_estudiante, id_asignatura))

        conexion.commit()
        cursor.close()
        conexion.close()

        flash("Sesión agregada correctamente", "success")
        return redirect(url_for("sesiones_list"))

    # Obtener monitores, estudiantes y asignaturas para mostrarlos en el formulario
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("SELECT id_monitor, nombre FROM monitor")
    monitores = cursor.fetchall()

    cursor.execute("SELECT id_estudiante, nombre FROM estudiante")
    estudiantes = cursor.fetchall()

    cursor.execute("SELECT id_asignatura, nombre_asignatura FROM asignatura")
    asignaturas = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "sesiones_form.html",
        modo="agregar",
        usuario=session.get("usuario"),
        monitores=monitores,
        estudiantes=estudiantes,
        asignaturas=asignaturas
    )

@app.route("/sesiones/eliminar/<int:id_sesion>")
def sesiones_eliminar(id_sesion):
    if "usuario" not in session:
        return redirect(url_for("login_view"))

    conexion = conectar()
    cursor = conexion.cursor()

    # 1. Verificar si la sesión tiene evidencias asociadas
    cursor.execute("SELECT COUNT(*) FROM evidencia WHERE id_sesion = %s", (id_sesion,))
    evidencias = cursor.fetchone()[0]

    if evidencias > 0:
        cursor.close()
        conexion.close()
        flash("No se puede eliminar esta sesión porque tiene evidencias asociadas. Primero elimine las evidencias.", "danger")
        return redirect(url_for("sesiones_list"))

    # 2. Eliminar sesión
    cursor.execute("DELETE FROM sesion_asesoria WHERE id_sesion = %s", (id_sesion,))
    conexion.commit()

    cursor.close()
    conexion.close()

    flash("Sesión eliminada correctamente", "success")
    return redirect(url_for("sesiones_list"))

@app.route("/sesiones/editar/<int:id_sesion>", methods=["GET", "POST"])
def sesiones_editar(id_sesion):
    if "usuario" not in session:
        return redirect(url_for("login_view"))

    conexion = conectar()
    cursor = conexion.cursor()

    # Obtener datos actuales
    cursor.execute("SELECT * FROM sesion_asesoria WHERE id_sesion = %s", (id_sesion,))
    sesion = cursor.fetchone()

    if not sesion:
        cursor.close()
        conexion.close()
        flash("La sesión no existe", "danger")
        return redirect(url_for("sesiones_list"))

    # Procesar actualización
    if request.method == "POST":
        fecha = request.form.get("fecha")
        hora_inicio = request.form.get("hora_inicio")
        hora_fin = request.form.get("hora_fin")
        id_estudiante = request.form.get("id_estudiante")
        id_monitor = request.form.get("id_monitor")
        id_asignatura = request.form.get("id_asignatura")
        tema = request.form.get("tema")

        cursor.execute("""
            UPDATE sesion_asesoria 
            SET fecha = %s,
                hora_inicio = %s,
                hora_fin = %s,
                id_estudiante = %s,
                id_monitor = %s,
                id_asignatura = %s,
                tema = %s
            WHERE id_sesion = %s
        """, (fecha, hora_inicio, hora_fin, id_estudiante, id_monitor, id_asignatura, tema, id_sesion))

        conexion.commit()
        cursor.close()
        conexion.close()

        flash("Sesión actualizada correctamente", "success")
        return redirect(url_for("sesiones_list"))

    # Cargar selects
    cursor.execute("SELECT id_estudiante, nombre FROM estudiante")
    estudiantes = cursor.fetchall()

    cursor.execute("SELECT id_monitor, nombre FROM monitor")
    monitores = cursor.fetchall()

    cursor.execute("SELECT id_asignatura, nombre_asignatura FROM asignatura")
    asignaturas = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template(
        "sesiones_form.html",
        modo="editar",
        sesion=sesion,
        estudiantes=estudiantes,
        monitores=monitores,
        asignaturas=asignaturas,
        usuario=session.get("usuario")
    )

@app.route("/evidencias")
def evidencias_list():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("""
        SELECT e.id_evidencia,
               e.descripcion,
               e.enlace_documento,
               s.tema AS sesion,
               s.fecha
        FROM evidencia e
        LEFT JOIN sesion_asesoria s ON e.id_sesion = s.id_sesion
        ORDER BY e.id_evidencia
    """)
    evidencias = cursor.fetchall()
    cursor.close()
    conexion.close()

    print("DEBUG - listado evidencias:", evidencias)  # Puedes quitarlo luego

    return render_template("evidencias.html", usuario=session.get("usuario"), evidencias=evidencias)

from flask import send_from_directory

@app.route("/uploads/<path:filename>")
def descargar(filename):
    carpeta = os.path.join(app.root_path, "static", "uploads")
    return send_from_directory(carpeta, filename, as_attachment=True)

# Ruta para agregar nueva evidencia
import os
from flask import Flask, render_template, request, redirect, url_for, session

@app.route("/evidencias/agregar", methods=["GET", "POST"])
def agregar_evidencia():
    if request.method == "POST":
        descripcion = request.form["descripcion"]
        archivo = request.files.get("archivo")
        id_sesion = request.form["id_sesion"]  # Asegúrate de enviarlo desde el formulario

        enlace_documento = None
        if archivo:
            nombre_archivo = archivo.filename
            carpeta = "static/uploads"
            os.makedirs(carpeta, exist_ok=True)  # crea la carpeta si no existe
            archivo.save(os.path.join(carpeta, nombre_archivo))
            enlace_documento = f"uploads/{nombre_archivo}"  # ruta relativa para guardar en DB

        # Insertar en la base de datos
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO evidencia (descripcion, enlace_documento, id_sesion) VALUES (%s, %s, %s)",
            (descripcion, enlace_documento, id_sesion)
        )
        conexion.commit()
        cursor.close()
        conexion.close()

        return redirect(url_for("evidencias_list"))

    # Para el GET, probablemente quieras enviar las sesiones disponibles
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT id_sesion, fecha FROM sesion_asesoria")
    sesiones = cursor.fetchall()
    cursor.close()
    conexion.close()

    return render_template("agregar_evidencia.html", sesiones=sesiones)


# Ruta para editar evidencia
@app.route("/evidencias/editar/<int:id_evidencia>", methods=["GET", "POST"])
def editar_evidencia(id_evidencia):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    if request.method == "POST":
        descripcion = request.form["descripcion"]
        id_sesion = request.form["id_sesion"]
        archivo = request.files.get("archivo")
        nombre_archivo = None

        if archivo and archivo.filename != "":
            nombre_archivo = archivo.filename
            archivo.save(f"static/uploads/{nombre_archivo}")

        if nombre_archivo:
            carpeta = "static/uploads"
            os.makedirs(carpeta, exist_ok=True)
            archivo.save(os.path.join(carpeta, nombre_archivo))
            enlace = f"uploads/{nombre_archivo}"  # ← mantener mismo formato que en agregar

            cursor.execute(
                "UPDATE evidencia SET descripcion=%s, enlace_documento=%s, id_sesion=%s WHERE id_evidencia=%s",
                (descripcion, enlace, id_sesion, id_evidencia)
            )

        else:
            cursor.execute(
                "UPDATE evidencia SET descripcion=%s, id_sesion=%s WHERE id_evidencia=%s",
                (descripcion, id_sesion, id_evidencia)
            )

        conexion.commit()
        cursor.close()
        conexion.close()
        return redirect(url_for("evidencias_list"))

    # GET: obtener datos de la evidencia
    cursor.execute("SELECT * FROM evidencia WHERE id_evidencia=%s", (id_evidencia,))
    evidencia = cursor.fetchone()

    # Obtener todas las sesiones para el select
    cursor.execute("SELECT id_sesion, tema FROM sesion_asesoria")
    sesiones = cursor.fetchall()

    cursor.close()
    conexion.close()

    return render_template("editar_evidencia.html", evidencia=evidencia, sesiones=sesiones)

# Ruta para eliminar evidencia
@app.route("/evidencias/eliminar/<int:id_evidencia>")
def eliminar_evidencia(id_evidencia):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM evidencia WHERE id_evidencia=%s", (id_evidencia,))
    conexion.commit()
    cursor.close()
    conexion.close()
    return redirect(url_for("evidencias_list"))

if __name__ == "__main__":
    app.run(debug=True)