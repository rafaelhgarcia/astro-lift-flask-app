from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import sqlite3
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
if not os.path.exists('logs'):
    os.makedirs('logs')

# Asegurarse de que existe el directorio para la base de datos
if not os.path.exists('instance'):
    os.makedirs('instance')

app = Flask(__name__)

# Configuración de logging
handler = RotatingFileHandler('logs/app.log', maxBytes=10000, backupCount=3)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)
handler.setFormatter(formatter)
app.logger.setLevel(logging.INFO)
app.logger.info('Iniciando aplicación')

# Configuración de Flask
app.secret_key = os.getenv('SECRET_KEY', 'mi_clave_secreta')

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/tareas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Verificar configuración de correo
required_mail_configs = ['MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']
missing_configs = [config for config in required_mail_configs if not os.getenv(config)]
if missing_configs:
    app.logger.error(f'Faltan configuraciones de correo: {", ".join(missing_configs)}')

# Configuración de Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

try:
    mail = Mail(app)
    app.logger.info('Configuración de correo inicializada correctamente')
except Exception as e:
    app.logger.error(f'Error al inicializar la configuración de correo: {str(e)}')

# Modelo de Tarea
class Tarea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(500))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    completada = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Tarea {self.titulo}>'

# Crear las tablas de la base de datos
with app.app_context():
    try:
        db.create_all()
        app.logger.info('Base de datos inicializada correctamente')
    except Exception as e:
        app.logger.error(f'Error al inicializar la base de datos: {str(e)}')

# Lista simple para almacenar tareas (temporal)
tareas = []

# Configuración de usuario administrador
ADMIN_USER = "admin"
ADMIN_PASSWORD = "admin"  # Contraseña en texto plano temporalmente

# Decorator para proteger rutas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def inicio():
    return render_template('index.html')

@app.route('/contacto')
def contacto():
    return render_template('contacto.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USER and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('intranet'))
        else:
            flash('Usuario o contraseña incorrectos')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/intranet')
@login_required
def intranet():
    return render_template('intranet.html', tareas=tareas)

@app.route('/agregar_tarea', methods=['POST'])
def agregar_tarea():
    try:
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        if titulo and descripcion:
            tarea = {
                'id': len(tareas) + 1,
                'titulo': titulo,
                'descripcion': descripcion,
                'completada': False
            }
            tareas.append(tarea)
            flash('¡Tarea agregada con éxito!', 'success')
        else:
            flash('Por favor completa todos los campos', 'danger')
    except Exception as e:
        flash('Error al agregar la tarea', 'danger')
    return redirect(url_for('intranet'))

@app.route('/completar_tarea/<int:id>')
def completar_tarea(id):
    try:
        for tarea in tareas:
            if tarea['id'] == id:
                tarea['completada'] = not tarea['completada']
                estado = "completada" if tarea['completada'] else "pendiente"
                flash(f'Tarea marcada como {estado}', 'success')
                break
    except Exception as e:
        flash('Error al actualizar la tarea', 'danger')
    return redirect(url_for('intranet'))

@app.route('/eliminar_tarea/<int:id>')
def eliminar_tarea(id):
    try:
        for tarea in tareas:
            if tarea['id'] == id:
                tareas.remove(tarea)
                flash('Tarea eliminada', 'success')
                break
    except Exception as e:
        flash('Error al eliminar la tarea', 'danger')
    return redirect(url_for('intranet'))

@app.route('/enviar_contacto', methods=['POST'])
def enviar_contacto():
    try:
        # Verificar configuración de correo
        if not all([app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'], app.config['MAIL_DEFAULT_SENDER']]):
            raise ValueError('Configuración de correo incompleta')

        # Obtener datos del formulario
        nombre = request.form.get('nombre')
        empresa = request.form.get('empresa')
        email = request.form.get('email')
        telefono = request.form.get('telefono')
        tipo_servicio = request.form.get('tipo_servicio')
        mensaje = request.form.get('mensaje')

        # Validar datos requeridos
        if not all([nombre, email, telefono, tipo_servicio, mensaje]):
            raise ValueError('Faltan campos requeridos')

        # Crear el cuerpo del correo
        body = f"""
        Nueva solicitud de contacto:
        
        Nombre: {nombre}
        Empresa: {empresa}
        Email: {email}
        Teléfono: {telefono}
        Tipo de Servicio: {tipo_servicio}
        
        Mensaje:
        {mensaje}
        """

        # Crear y enviar el correo
        msg = Message(
            subject=f'Nueva solicitud de contacto de {nombre}',
            recipients=[app.config['MAIL_DEFAULT_SENDER']],
            body=body,
            reply_to=email
        )
        
        mail.send(msg)
        app.logger.info(f'Correo enviado exitosamente para {email}')

        # Enviar correo de confirmación al cliente
        confirmation_msg = Message(
            subject='Hemos recibido tu mensaje',
            recipients=[email],
            body=f"""
            Estimado/a {nombre},

            Gracias por contactarnos. Hemos recibido tu mensaje y nos pondremos en contacto contigo lo antes posible.

            Detalles de tu solicitud:
            - Tipo de servicio: {tipo_servicio}
            - Mensaje: {mensaje}

            Saludos cordiales,
            Equipo de Servicios de Elevación
            """
        )
        mail.send(confirmation_msg)
        app.logger.info(f'Correo de confirmación enviado a {email}')

        flash('¡Mensaje enviado con éxito! Te contactaremos pronto.', 'success')
    except ValueError as e:
        app.logger.error(f'Error de validación: {str(e)}')
        flash('Por favor, verifica que todos los campos estén completos.', 'danger')
    except Exception as e:
        app.logger.error(f'Error al enviar el correo: {str(e)}')
        flash('Hubo un error al enviar el mensaje. Por favor, intenta nuevamente.', 'danger')

    return redirect(url_for('contacto'))

@app.errorhandler(404)
def not_found_error(error):
    app.logger.error(f'Página no encontrada: {request.url}')
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    app.logger.error(f'Error del servidor: {str(error)}')
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Asegurarse de que el directorio static existe
    if not os.path.exists('static'):
        os.makedirs('static')
    if not os.path.exists('static/images'):
        os.makedirs('static/images')
    
    # Iniciar el servidor
    app.run(debug=True, host='127.0.0.1', port=5000) 