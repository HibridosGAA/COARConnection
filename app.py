from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash 
from datetime import datetime

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
    # Campo para marcar administradores
    is_admin = db.Column(db.Boolean, default=False)
    # Fecha de creación del usuario
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Método para cifrar la contraseña
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Método para verificar la contraseña
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} (admin={self.is_admin})>'

# Modelo para contactos/amigos
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    owner = db.relationship('User', foreign_keys=[owner_id], backref='owned_contacts')
    contact = db.relationship('User', foreign_keys=[contact_id])

# Crea la base de datos y las tablas (solo la primera vez)
with app.app_context():
    db.create_all()

# ----------------------------------------
# RUTAS
# ----------------------------------------

@app.route('/')
def home():
    # Si el usuario ya está logueado, redirigir al dashboard
    if 'username' in session:
        return redirect(url_for('dashboard'))
    
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

# Ruta para INICIAR SESIÓN
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()

    # 1. Verificar si el usuario existe y si la contraseña es correcta
    if user and user.check_password(password):
        # 2. Iniciar sesión: Guardar el nombre de usuario en la sesión de Flask
        session['username'] = user.username
        flash(f'¡Bienvenido, {user.username}!', 'success')
        return redirect(url_for('dashboard'))
    else:
        # 3. Mostrar error y redirigir de vuelta al login
        flash('Nombre de usuario o contraseña incorrectos.', 'error')
        return redirect(url_for('home'))

# Nueva ruta para la ZONA PRIVADA
@app.route('/dashboard')
def dashboard():
    # Requerir que el usuario haya iniciado sesión
    if 'username' not in session:
        flash('Debes iniciar sesión para acceder a esta página.', 'error')
        return redirect(url_for('home'))
    # Obtener el usuario actual
    user = User.query.filter_by(username=session['username']).first()

    # Obtener la lista de contactos (solo los nombres de usuario)
    contacts = []
    if user:
        # join Contact -> User para obtener los usernames de los contact_id
        results = Contact.query.filter_by(owner_id=user.id).join(User, Contact.contact_id == User.id).add_columns(User.username).all()
        # results es lista de tuplas (Contact, username) porque usamos add_columns
        contacts = [r[1] for r in results]

    # Pasar el nombre de usuario y la lista de contactos a la plantilla
    return render_template('dashboard.html', username=session['username'], contacts=contacts)

# Ruta para EDITAR PERFIL
@app.route('/editar')
def editar():
    # Requerir que el usuario haya iniciado sesión para editar el perfil
    if 'username' not in session:
        flash('Debes iniciar sesión para editar el perfil.', 'error')
        return redirect(url_for('home'))

    # Renderiza la plantilla de editar perfil
    return render_template('editar.html', username=session.get('username'))


# RUTA: Página de administración con la lista de usuarios (solo admin)
@app.route('/admin/users')
def admin_users():
    if 'username' not in session:
        flash('Debes iniciar sesión.', 'error')
        return redirect(url_for('home'))

    current = User.query.filter_by(username=session['username']).first()
    if not current or not current.is_admin:
        flash('Acceso denegado. Necesitas permisos de administrador.', 'error')
        return redirect(url_for('dashboard'))

    users = User.query.order_by(User.created_at.desc()).all()
    # No enviar password_hash al front-end si no es necesario; se muestra solo username y fecha
    return render_template('register.html', users=users)


# RUTA: Admin establece/resetear contraseña para un usuario (POST)
@app.route('/admin/set_password', methods=['POST'])
def admin_set_password():
    if 'username' not in session:
        flash('Debes iniciar sesión.', 'error')
        return redirect(url_for('home'))

    current = User.query.filter_by(username=session['username']).first()
    if not current or not current.is_admin:
        flash('Acceso denegado. Necesitas permisos de administrador.', 'error')
        return redirect(url_for('dashboard'))

    target_username = request.form.get('target_username', '').strip()
    new_password = request.form.get('new_password', '').strip()

    if not target_username or not new_password:
        flash('Debes proporcionar usuario y nueva contraseña.', 'error')
        return redirect(url_for('admin_users'))

    target = User.query.filter_by(username=target_username).first()
    if not target:
        flash('Usuario objetivo no encontrado.', 'error')
        return redirect(url_for('admin_users'))

    # Cambiar la contraseña (se guarda como hash)
    target.set_password(new_password)
    db.session.commit()

    flash(f'Contraseña de {target.username} actualizada correctamente.', 'success')
    return redirect(url_for('admin_users'))


# Página de login de administrador (solo para credenciales especiales)
@app.route('/admin')
def admin_login_page():
    # Si ya está logeado como admin, redirigir a la lista
    if 'username' in session:
        u = User.query.filter_by(username=session['username']).first()
        if u and u.is_admin:
            return redirect(url_for('admin_users'))
    return render_template('admin.html')


# Procesa login admin (credenciales fijas: admin / hh)
@app.route('/admin/login', methods=['POST'])
def admin_login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')

    # Credenciales fijas según la petición
    if username == 'admin' and password == 'hh':
        # Asegurar que exista el usuario admin en la BD y marcar como admin
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(username='admin')
            # guardar una contraseña segura: la seteamos a 'hh' hasheada
            admin_user.set_password('hh')
            admin_user.is_admin = True
            db.session.add(admin_user)
            db.session.commit()
        else:
            # Marcar como admin si no lo está
            if not admin_user.is_admin:
                admin_user.is_admin = True
                db.session.commit()

        # Iniciar sesión como admin
        session['username'] = 'admin'
        flash('Acceso administrador concedido.', 'success')
        return redirect(url_for('admin_users'))

    flash('Credenciales de administrador incorrectas.', 'error')
    return redirect(url_for('admin_login_page'))


# Ruta para AÑADIR AMIGOS / contactos
@app.route('/add_friend', methods=['POST'])
def add_friend():
    if 'username' not in session:
        flash('Debes iniciar sesión para agregar amigos.', 'error')
        return redirect(url_for('home'))

    contact_username = request.form.get('contact_username', '').strip()
    if not contact_username:
        flash('Por favor ingresa un nombre de usuario válido.', 'error')
        return redirect(url_for('dashboard'))

    # No permite agregarse a sí mismo
    if contact_username == session['username']:
        flash('No puedes agregarte a ti mismo.', 'error')
        return redirect(url_for('dashboard'))

    contact_user = User.query.filter_by(username=contact_username).first()
    if not contact_user:
        flash('Usuario no encontrado. Asegúrate de que el nombre esté escrito correctamente.', 'error')
        return redirect(url_for('dashboard'))

    owner = User.query.filter_by(username=session['username']).first()
    # Comprobar duplicados
    existing = Contact.query.filter_by(owner_id=owner.id, contact_id=contact_user.id).first()
    if existing:
        flash('Ya agregaste a ese usuario.', 'error')
        return redirect(url_for('dashboard'))

    # Crear el contacto
    new_contact = Contact(owner_id=owner.id, contact_id=contact_user.id)
    db.session.add(new_contact)
    db.session.commit()

    flash(f'Has agregado a {contact_user.username} como amigo.', 'success')
    return redirect(url_for('dashboard'))

# Nueva ruta para CERRAR SESIÓN
@app.route('/logout')
def logout():
    # Eliminar el nombre de usuario de la sesión
    session.pop('username', None)
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
