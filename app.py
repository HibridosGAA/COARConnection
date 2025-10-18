from flask import Flask, render_template

# Crea una instancia de la aplicación Flask
app = Flask(__name__)

# Define una ruta (la página de inicio)
@app.route('/')
def home():
    # Renderiza la plantilla HTML llamada 'index.html'
    return render_template('index.html')

# (Opcional, pero bueno para pruebas locales)
if __name__ == '__main__':
    app.run(debug=True)