import os

class Config:
    SECRET_KEY = 'tu_clave_secreta_aqui'
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    # Aseguramos que la ruta de la base de datos sea absoluta
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'tareas.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración del correo
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'info@astroliftrental.com'
    MAIL_PASSWORD = 'tu_contraseña_aqui'
    MAIL_DEFAULT_SENDER = 'info@astroliftrental.com' 