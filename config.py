import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tu-clave-secreta-muy-segura-aqui'
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    # Aseguramos que la ruta de la base de datos sea absoluta
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///tareas.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de correo con valores predeterminados
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'astrolift@ejemplo.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'password_temporal'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'astrolift@ejemplo.com' 