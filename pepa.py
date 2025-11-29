import mysql.connector
from mysql.connector import Error
import pandas as pd
import os

# --- Conexión a la base de datos ---
def conectar():
    try:
        conexion = mysql.connector.connect(
            host='localhost',
            user='root',
            password='pila245A*',
            database='pepa'
        )
        if conexion.is_connected():
            return conexion
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None

# --- Funciones para usuarios ---
def validar_usuario(conexion, nombre_usuario, contrasena):
    try:
        cursor = conexion.cursor()
        sql = "SELECT * FROM usuario WHERE nombre_usuario = %s AND contrasena = %s"
        cursor.execute(sql, (nombre_usuario, contrasena))
        resultado = cursor.fetchone()
        return resultado
    except Error as e:
        print("Error al validar usuario:", e)
        return None

def insertar_usuario(conexion, nombre_usuario, contrasena, nombre_completo=None, email=None):
    try:
        cursor = conexion.cursor()
        sql = """INSERT INTO usuario (nombre_usuario, contrasena, nombre_completo, email) 
                 VALUES (%s, %s, %s, %s)"""
        valores = (nombre_usuario, contrasena, nombre_completo, email)
        cursor.execute(sql, valores)
        conexion.commit()
        print("Usuario creado con ID:", cursor.lastrowid)
    except Error as e:
        print("Error al insertar usuario:", e)

# --- Funciones para programa ---
def insertar_programa(conexion, nombre_programa):
    try:
        cursor = conexion.cursor()
        sql = "INSERT INTO programa (nombre_programa) VALUES (%s)"
        cursor.execute(sql, (nombre_programa,))
        conexion.commit()
        return cursor.lastrowid
    except Error as e:
        print("Error al insertar programa:", e)
        return None

def mostrar_programas(conexion):
    try:
        cursor = conexion.cursor()
        cursor.execute("SELECT id_programa, nombre_programa FROM programa")
        programas = cursor.fetchall()
        return programas
    except Error as e:
        print("Error al obtener programas:", e)
        return []

# --- Funciones para monitor ---
def insertar_monitor(conexion, id_usuario, telefono, programa_id, nombre, apellido, cedula, email):
    try:
        cursor = conexion.cursor()
        sql = """INSERT INTO monitor (id_usuario, telefono, programa_id, nombre, apellido, cedula, email)
                 VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        valores = (id_usuario, telefono, programa_id, nombre, apellido, cedula, email)
        cursor.execute(sql, valores)
        conexion.commit()
        return cursor.lastrowid
    except Error as e:
        print("Error al insertar monitor:", e)
        return None

def mostrar_monitores(conexion, id_usuario):
    try:
        cursor = conexion.cursor()
        sql = """
            SELECT m.id_monitor, m.id_usuario, m.telefono, p.nombre_programa, m.nombre, m.apellido, m.email
            FROM monitor m
            LEFT JOIN programa p ON m.programa_id = p.id_programa
        """
        cursor.execute(sql)
        return cursor.fetchall()
    except Error as e:
        print("Error mostrando monitores:", e)
        return []

# --- Funciones para estudiante ---
def insertar_estudiante(conexion, nombre, apellido, cedula, telefono, email, id_programa):
    try:
        cursor = conexion.cursor()
        sql = """INSERT INTO estudiante (nombre, apellido, cedula, telefono, email, id_programa)
                 VALUES (%s, %s, %s, %s, %s, %s)"""
        valores = (nombre, apellido, cedula, telefono, email, id_programa)
        cursor.execute(sql, valores)
        conexion.commit()
        return cursor.lastrowid
    except Error as e:
        print("Error al insertar estudiante:", e)
        return None

def mostrar_estudiantes(conexion):
    try:
        cursor = conexion.cursor()
        query = """
        SELECT est.id_estudiante, est.nombre, est.apellido, est.cedula, est.telefono, est.email, p.nombre_programa
        FROM estudiante est
        JOIN programa p ON est.id_programa = p.id_programa
        ORDER BY est.id_estudiante
        """
        cursor.execute(query)
        datos = cursor.fetchall()
        cursor.close()
        return datos  
    except Error as e:
        print("Error al mostrar estudiantes:", e)
        return []  

# --- Funciones para asignatura ---
def insertar_asignatura(conexion, nombre_asignatura, semestre, id_programa):
    try:
        cursor = conexion.cursor()
        sql = """INSERT INTO asignatura (nombre_asignatura, semestre, id_programa)
                 VALUES (%s, %s, %s)"""
        valores = (nombre_asignatura, semestre, id_programa)
        cursor.execute(sql, valores)
        conexion.commit()
        return cursor.lastrowid
    except Error as e:
        print("Error al insertar asignatura:", e)
        return None

def mostrar_asignaturas(conexion):
    try:
        cursor = conexion.cursor()
        query = """
        SELECT asi.id_asignatura, asi.nombre_asignatura, asi.semestre, p.nombre_programa
        FROM asignatura asi
        JOIN programa p ON asi.id_programa = p.id_programa
        """
        cursor.execute(query)
        return cursor.fetchall()
    except Error as e:
        print("Error al mostrar asignaturas:", e)
        return []

# --- Funciones para sesión de asesoría ---
def insertar_sesion_asesoria(conexion, fecha, hora_inicio, hora_fin, tema, id_monitor, id_estudiante, id_asignatura):
    try:
        cursor = conexion.cursor()
        sql = """INSERT INTO sesion_asesoria (fecha, hora_inicio, hora_fin, tema, id_monitor, id_estudiante, id_asignatura)
                 VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        valores = (fecha, hora_inicio, hora_fin, tema, id_monitor, id_estudiante, id_asignatura)
        cursor.execute(sql, valores)
        conexion.commit()
        return cursor.lastrowid
    except Error as e:
        print("Error al insertar sesión:", e)
        return None

# --- Funciones para evidencia ---
from werkzeug.utils import secure_filename

def insertar_evidencia(conexion, id_sesion, descripcion, url_archivo):
    try:
        # Asegurar un nombre válido
        nombre_archivo = secure_filename(os.path.basename(url_archivo))

        # Guardar en la carpeta /static/uploads
        carpeta = os.path.join(os.getcwd(), "static", "uploads")
        os.makedirs(carpeta, exist_ok=True)

        archivo_real = os.path.join(carpeta, nombre_archivo)
        # Si el archivo no está guardado aún, guardarlo
        if not os.path.exists(archivo_real) and os.path.exists(url_archivo):
            from shutil import copy2
            copy2(url_archivo, archivo_real)

        # Guardar en BD la ruta relativa correcta
        enlace_documento = f"uploads/{nombre_archivo}"

        cursor = conexion.cursor()
        sql = "INSERT INTO evidencia (descripcion, enlace_documento, id_sesion) VALUES (%s, %s, %s)"
        valores = (descripcion, enlace_documento, id_sesion)
        cursor.execute(sql, valores)
        conexion.commit()
        cursor.close()
        return True

    except Error as e:
        print("Error al insertar evidencia:", e)
        return False

def mostrar_evidencias(conexion):
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT e.id_evidencia,
                   e.descripcion,
                   e.enlace_documento,
                   s.tema AS sesion,
                   s.fecha
            FROM evidencia e
            JOIN sesion_asesoria s ON e.id_sesion = s.id_sesion
            ORDER BY e.id_evidencia
        """)
        datos = cursor.fetchall()
        cursor.close()
        return datos
    except Error as e:
        print("Error al mostrar evidencias:", e)
        return []

# --- Función para descargar Excel sin interfaz ---
def generar_excel_usuario(conexion, id_usuario):
    try:
        cursor = conexion.cursor(dictionary=True)
        query = "SELECT * FROM evidencia WHERE id_sesion IN (SELECT id_sesion FROM sesion_asesoria WHERE id_monitor = %s)"
        cursor.execute(query, (id_usuario,))
        datos = cursor.fetchall()
        if not datos:
            return None

        df = pd.DataFrame(datos)
        nombre = f"evidencias_usuario_{id_usuario}.xlsx"
        ruta = os.path.join(os.getcwd(), nombre)
        df.to_excel(ruta, index=False)
        return ruta
    except:
        return None