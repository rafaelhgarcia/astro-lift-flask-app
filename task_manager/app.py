from flask import Flask, render_template, request, flash, redirect, url_for
from datetime import datetime

# Crear la aplicación Flask
app = Flask(__name__)
app.secret_key = 'mi_clave_secreta'  # Necesario para mensajes flash y sesiones

# Lista para almacenar las tareas (simulando una base de datos)
tareas = []

# Definir la ruta principal
@app.route('/')
def inicio():
    return render_template('index.html', tareas=tareas, fecha_actual=datetime.now())

@app.route('/agregar_tarea', methods=['POST'])
def agregar_tarea():
    titulo = request.form.get('titulo')
    descripcion = request.form.get('descripcion')
    if titulo and descripcion:
        tarea = {
            'id': len(tareas) + 1,
            'titulo': titulo,
            'descripcion': descripcion,
            'fecha': datetime.now(),
            'completada': False
        }
        tareas.append(tarea)
        flash('¡Tarea agregada con éxito!', 'success')
    else:
        flash('Por favor completa todos los campos', 'error')
    return redirect(url_for('inicio'))

@app.route('/completar_tarea/<int:id>')
def completar_tarea(id):
    for tarea in tareas:
        if tarea['id'] == id:
            tarea['completada'] = not tarea['completada']
            flash('Estado de la tarea actualizado', 'success')
            break
    return redirect(url_for('inicio'))

@app.route('/eliminar_tarea/<int:id>')
def eliminar_tarea(id):
    for tarea in tareas:
        if tarea['id'] == id:
            tareas.remove(tarea)
            flash('Tarea eliminada', 'success')
            break
    return redirect(url_for('inicio'))

@app.route('/acerca')
def acerca():
    return render_template('acerca.html')

# Iniciar la aplicación si este archivo es el principal
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000) 