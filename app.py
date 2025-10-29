from flask import Flask, render_template, request, url_for, redirect, flash, session
from pymongo import MongoClient
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

client = MongoClient(
    'localhost',
    27017,
    username=os.getenv("USERNAME"),
    password=os.getenv("PASSWORD"),
    authSource='admin'
)

db = client.prueba
manuel = db.manuel
usuarios = db.usuarios


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = usuarios.find_one({'username': username, 'password': password})

        if user:
            session['usuario'] = username
            session['rol'] = user.get('rol', 'usuario')
            flash(f'Bienvenido, {username}')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada')
    return redirect(url_for('login'))


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    rol = session.get('rol')

    # Si es admin y envía formulario → insertar
    if request.method == 'POST' and rol == 'admin':
        nombre = request.form['user']
        edad = request.form['edad']
        localidad = request.form['localidad']
        manuel.insert_one({'nombre': nombre, 'edad': edad, 'localidad': localidad})
        flash('Registro insertado correctamente')
        return redirect(url_for('index'))

    # Filtrado de búsqueda
    filtro = {}
    if request.args:
        nombre = request.args.get('nombre')
        edad = request.args.get('edad')
        localidad = request.args.get('localidad')

        if nombre:
            filtro['nombre'] = {'$regex': nombre, '$options': 'i'}
        if edad:
            filtro['edad'] = edad
        if localidad:
            filtro['localidad'] = {'$regex': localidad, '$options': 'i'}

    all_docs = list(manuel.find(filtro))
    return render_template('index.html', coleccion=all_docs, usuario=session['usuario'], rol=rol, filtro=filtro)


@app.route('/delete/<id>')
def delete(id):
    from bson.objectid import ObjectId
    if 'usuario' not in session or session.get('rol') != 'admin':
        flash('No tienes permiso para eliminar registros')
        return redirect(url_for('index'))

    manuel.delete_one({'_id': ObjectId(id)})
    flash('Registro eliminado correctamente')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
