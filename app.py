from flask import Flask, render_template, request, redirect, url_for, flash # Importado 'flash'
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Inicialización de la aplicación
app = Flask(__name__)

# ----------------------------------------
# CONFIGURACIÓN ADICIONAL NECESARIA PARA 'flash'
# ----------------------------------------
# CLAVE SECRETA NECESARIA PARA USAR SESSIONS/FLASH
app.config['SECRET_KEY'] = 'una_clave_secreta_fuerte_aqui' 

# ----------------------------------------
# CONFIGURACIÓN DE LA BASE DE DATOS
# Usaremos SQLite. 'usuarios.db' se creará en el mismo directorio.
# ----------------------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///usuarios.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ----------------------------------------
# MODELO DE LA BASE DE DATOS (TABLA User)
# ----------------------------------------
class User(db.Model):
    # Clave primaria autoincremental
    id = db.Column(db.Integer, primary_key=True)
    # Nombre de usuario único, obligatorio y de máximo 80 caracteres
    username = db.Column(db.String(80), unique=True, nullable=False)
    # Almacena el hash (cifrado) de la contraseña
    password_hash = db.Column(db.String(128), nullable=False)

    # Método para cifrar la contraseña antes de guardarla
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Método para verificar si la contraseña proporcionada es correcta
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Representación de cadena útil para depuración
    def __repr__(self):
        return f'<User {self.username}>'

# Crea la base de datos y las tablas (ejecutar solo al inicio)
with app.app_context():
    db.create_all()

# ----------------------------------------
# RUTAS DE LA APLICACIÓN
# ----------------------------------------

# 1. Ruta principal (página de inicio)
@app.route('/')
def home():
    # Ahora la ruta principal muestra el formulario de login/registro (login.html).
    return render_template('login.html')

# 2. Ruta de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # 1. Obtener datos del formulario
        username = request.form.get('username')
        password = request.form.get('password')

        # Manejo básico de errores: campos vacíos
        if not username or not password:
            flash("Error: Nombre de usuario o contraseña no pueden estar vacíos.", 'error')
            return redirect(url_for('register'))

        # 2. Verificar si el usuario ya existe
        if User.query.filter_by(username=username).first():
            # Muestra el mensaje flash de error
            flash('El nombre de usuario ya existe. Inténtalo de nuevo', 'error')
            return redirect(url_for('register')) # Redirige al GET para mostrar el mensaje

        # 3. Crear el nuevo usuario y cifrar la contraseña
        new_user = User(username=username)
        new_user.set_password(password) # Cifra la contraseña antes de asignarla

        # 4. Guardar en la base de datos
        db.session.add(new_user)
        db.session.commit()

        # Opcional: Mostrar mensaje de éxito
        flash('¡Cuenta creada con éxito! Por favor, inicia sesión.', 'success')

        # 5. Redirigir a la página principal (que ahora es el login)
        return redirect(url_for('home'))

    # Si es un método GET (acceso directo a /register), sigue mostrando el formulario
    return render_template('login.html')

# ----------------------------------------
# INICIO DEL SERVIDOR
# ----------------------------------------
if __name__ == '__main__':
    # Nota: Render ejecuta la app con Gunicorn. Esto es para pruebas locales.
    app.run(debug=True)
