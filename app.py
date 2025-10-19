from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash 

app = Flask(__name__)

# **********************************************
# FIX 1: Configuración de la Clave Secreta
# La SECRET_KEY es necesaria para usar 'flash' (mensajes temporales)
# y para mantener la sesión segura. Usa una cadena compleja en producción.
app.config['SECRET_KEY'] = 'una_clave_secreta_super_segura_12345'
# **********************************************

# Configuración de la Base de Datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///usuarios.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ----------------------------------------
# MODELO DE LA BASE DE DATOS
# ----------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # Método para cifrar la contraseña
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Método para verificar la contraseña
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# Crea la base de datos y las tablas (solo la primera vez)
with app.app_context():
    db.create_all()

# ----------------------------------------
# RUTAS
# ----------------------------------------

@app.route('/')
def home():
    # Muestra el formulario de login/registro al entrar a la URL raíz
    return render_template('login.html')

# Ruta para el REGISTRO de usuarios
@app.route('/register', methods=['POST'])
def register():
    # Esta ruta solo acepta POST desde el formulario de registro
    username = request.form.get('username')
    password = request.form.get('password')

    if User.query.filter_by(username=username).first():
        # Usa flash para mostrar el mensaje de error en la plantilla
        flash('El nombre de usuario ya existe. Inténtalo de nuevo', 'error')
        return redirect(url_for('home'))

    # Crear el nuevo usuario y cifrar la contraseña
    new_user = User(username=username)
    new_user.set_password(password)

    # Guardar en la base de datos
    db.session.add(new_user)
    db.session.commit()
    
    flash('¡Cuenta creada con éxito! Por favor, inicia sesión.', 'success')
    return redirect(url_for('home')) # Redirige de vuelta a la página de login/registro

# **********************************************
# FIX 2: Nueva Ruta para INICIAR SESIÓN
# Esta ruta evita el error 500 al hacer submit en el formulario de login.
# **********************************************
@app.route('/login', methods=['POST'])
def login():
    # Por ahora, esta ruta solo evita el error y redirige.
    # La lógica real de verificación de credenciales se implementaría aquí.
    
    # username = request.form.get('username')
    # password = request.form.get('password')
    
    flash('Funcionalidad de inicio de sesión aún no implementada. Redirigiendo...', 'error')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
