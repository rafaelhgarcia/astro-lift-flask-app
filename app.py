from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from config import Config

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
if not os.path.exists('logs'):
    os.makedirs('logs')

# Asegurarse de que existe el directorio para la base de datos
instance_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'instance'))
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

app = Flask(__name__)

# Configurar logging
handler = RotatingFileHandler('logs/app.log', maxBytes=10000, backupCount=3, mode='a')
handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
))
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Iniciando aplicación')

# Configuración de Flask
app.secret_key = os.getenv('SECRET_KEY', 'mi_clave_secreta')

# Configuración de la base de datos
# En producción usa PostgreSQL, en desarrollo SQLite
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Render/PostgreSQL
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Desarrollo local/SQLite
    db_path = os.path.join(instance_path, 'tareas.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar SQLAlchemy
db = SQLAlchemy(app)

# Usar configuración desde config.py
app.config.from_object(Config)

# Inicializar Flask-Mail (siempre funcional para desarrollo)
try:
    mail = Mail(app)
    app.logger.info('Configuración de correo inicializada correctamente')
except Exception as e:
    app.logger.warning(f'Configuración de correo usando valores por defecto: {str(e)}')

# Decorador para requerir autenticación
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicie sesión para acceder a esta página', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Modelo de Tarea
class Tarea(db.Model):
    __tablename__ = 'tarea'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(500))
    fecha = db.Column(db.DateTime, default=datetime.now)
    completada = db.Column(db.Boolean, default=False)
    serial_maquina = db.Column(db.String(100), nullable=True)
    observaciones = db.Column(db.Text, nullable=True)
    # Nuevos campos para datos del cliente y fotos
    nombre = db.Column(db.String(100), nullable=True)
    apellido = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    telefono = db.Column(db.String(50), nullable=True)
    direccion = db.Column(db.String(200), nullable=True)
    ciudad = db.Column(db.String(100), nullable=True)
    foto1_url = db.Column(db.String(200), nullable=True)
    foto2_url = db.Column(db.String(200), nullable=True)
    fecha_inicio = db.Column(db.Date, nullable=True)
    fecha_final = db.Column(db.Date, nullable=True)
    hora_inicio = db.Column(db.Time, nullable=True)
    hora_fin = db.Column(db.Time, nullable=True)

    def __repr__(self):
        return f'<Tarea {self.titulo}>'

# Modelo de Usuario
class Usuario(db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Crear las tablas de la base de datos
def init_db():
    try:
        # Asegurarse de que el directorio instance existe
        if not os.path.exists('instance'):
            os.makedirs('instance')
        
        # Crear todas las tablas con el nuevo campo
        db.create_all()
        
        # Agregar columna serial_maquina si no existe (migración simple)
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE tarea ADD COLUMN serial_maquina VARCHAR(100)"))
                conn.commit()
                app.logger.info('Columna serial_maquina agregada exitosamente')
        except Exception:
            # La columna ya existe o hubo un error
            pass
            
        # Agregar columna observaciones si no existe
        try:
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE tarea ADD COLUMN observaciones TEXT"))
                conn.commit()
                app.logger.info('Columna observaciones agregada exitosamente')
        except Exception:
            # La columna ya existe o hubo un error
            pass
            
        app.logger.info(f'Base de datos inicializada correctamente en {db_path}')
        return True
    except Exception as e:
        app.logger.error(f'Error al inicializar la base de datos: {str(e)}')
        return False

# Inicializar la base de datos
with app.app_context():
    init_db()
    # Crear usuario administrador si no existe
    admin_user = Usuario.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = Usuario(username='admin')
        admin_user.set_password('AstroLift2024')
        db.session.add(admin_user)
        db.session.commit()
        app.logger.info('Usuario administrador creado')

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
        
        user = Usuario.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('intranet'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('inicio'))

@app.route('/intranet')
@login_required
def intranet():
    # Obtener filtros desde la URL
    filtro_fecha = request.args.get('filtro_fecha')
    filtro_cliente = request.args.get('filtro_cliente')

    # Construir la consulta base
    query = Tarea.query

    # Aplicar filtro por fecha (fecha_inicio o fecha_final)
    if filtro_fecha:
        query = query.filter(
            (Tarea.fecha_inicio == filtro_fecha) | (Tarea.fecha_final == filtro_fecha)
        )

    # Aplicar filtro por nombre de cliente (nombre o apellido)
    if filtro_cliente:
        query = query.filter(
            (Tarea.nombre.ilike(f"%{filtro_cliente}%")) | (Tarea.apellido.ilike(f"%{filtro_cliente}%"))
        )

    tareas = query.order_by(Tarea.fecha.desc()).all()
    return render_template('intranet.html', tareas=tareas)

@app.route('/agregar_tarea', methods=['POST'])
def agregar_tarea():
    try:
        # Datos del formulario
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')
        serial_maquina = request.form.get('serial_maquina')
        observaciones = request.form.get('observaciones')
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        email = request.form.get('email')
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')
        ciudad = request.form.get('ciudad')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_final = request.form.get('fecha_final')
        hora_inicio = request.form.get('hora_inicio')
        hora_fin = request.form.get('hora_fin')

        # Manejo de fotos
        foto1 = request.files.get('foto1')
        foto2 = request.files.get('foto2')
        foto1_url = None
        foto2_url = None

        # Guardar foto1 si existe
        if foto1 and foto1.filename:
            foto1_path = os.path.join('static/images', foto1.filename)
            foto1.save(foto1_path)
            foto1_url = f'images/{foto1.filename}'

        # Guardar foto2 si existe
        if foto2 and foto2.filename:
            foto2_path = os.path.join('static/images', foto2.filename)
            foto2.save(foto2_path)
            foto2_url = f'images/{foto2.filename}'

        if titulo and descripcion:
            nueva_tarea = Tarea(
                titulo=titulo,
                descripcion=descripcion,
                fecha=datetime.now(),
                serial_maquina=serial_maquina,
                observaciones=observaciones,
                nombre=nombre,
                apellido=apellido,
                email=email,
                telefono=telefono,
                direccion=direccion,
                ciudad=ciudad,
                foto1_url=foto1_url,
                foto2_url=foto2_url,
                fecha_inicio=fecha_inicio if fecha_inicio else None,
                fecha_final=fecha_final if fecha_final else None,
                hora_inicio=hora_inicio if hora_inicio else None,
                hora_fin=hora_fin if hora_fin else None
            )
            db.session.add(nueva_tarea)
            db.session.commit()
            flash('¡Tarea agregada con éxito!', 'success')
        else:
            flash('Por favor completa todos los campos obligatorios', 'danger')
    except Exception as e:
        db.session.rollback()
        flash('Error al agregar la tarea', 'danger')
        app.logger.error(f'Error al agregar tarea: {str(e)}')
    return redirect(url_for('intranet'))

@app.route('/completar_tarea/<int:id>')
def completar_tarea(id):
    try:
        tarea = Tarea.query.get_or_404(id)
        tarea.completada = not tarea.completada
        db.session.commit()
        estado = "completada" if tarea.completada else "pendiente"
        flash(f'Tarea marcada como {estado}', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al actualizar la tarea', 'danger')
        app.logger.error(f'Error al completar tarea: {str(e)}')
    return redirect(url_for('intranet'))

@app.route('/eliminar_tarea/<int:id>')
def eliminar_tarea(id):
    try:
        tarea = Tarea.query.get_or_404(id)
        db.session.delete(tarea)
        db.session.commit()
        flash('Tarea eliminada', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar la tarea', 'danger')
        app.logger.error(f'Error al eliminar tarea: {str(e)}')
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
            Equipo de Astro Lift Rental
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

@app.route('/revisar_tarea/<int:id>')
@login_required
def revisar_tarea(id):
    tarea = Tarea.query.get_or_404(id)
    return render_template('revisar_tarea.html', tarea=tarea)

@app.route('/editar_tarea/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_tarea(id):
    tarea = Tarea.query.get_or_404(id)
    if request.method == 'POST':
        tarea.titulo = request.form.get('titulo')
        tarea.descripcion = request.form.get('descripcion')
        tarea.serial_maquina = request.form.get('serial_maquina')
        tarea.observaciones = request.form.get('observaciones')
        tarea.nombre = request.form.get('nombre')
        tarea.apellido = request.form.get('apellido')
        tarea.email = request.form.get('email')
        tarea.telefono = request.form.get('telefono')
        tarea.direccion = request.form.get('direccion')
        tarea.ciudad = request.form.get('ciudad')
        tarea.fecha_inicio = request.form.get('fecha_inicio')
        tarea.fecha_final = request.form.get('fecha_final')
        tarea.hora_inicio = request.form.get('hora_inicio')
        tarea.hora_fin = request.form.get('hora_fin')
        foto1 = request.files.get('foto1')
        foto2 = request.files.get('foto2')
        if foto1 and foto1.filename:
            foto1_path = os.path.join('static/images', foto1.filename)
            foto1.save(foto1_path)
            tarea.foto1_url = f'images/{foto1.filename}'
        if foto2 and foto2.filename:
            foto2_path = os.path.join('static/images', foto2.filename)
            foto2.save(foto2_path)
            tarea.foto2_url = f'images/{foto2.filename}'
        db.session.commit()
        flash('Servicio actualizado correctamente', 'success')
        return redirect(url_for('intranet'))
    return render_template('editar_tarea.html', tarea=tarea)

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
    
    # Configuración para desarrollo vs producción
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    # Iniciar el servidor
    app.run(debug=debug, host='0.0.0.0', port=port) 