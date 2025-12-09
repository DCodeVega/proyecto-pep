from flask import Flask, render_template, request, redirect, url_for, flash
import os
import sqlite3
from config import Config

# Inicializar la aplicación Flask
app = Flask(__name__)
app.config.from_object(Config)

# Función para conectar a la base de datos
def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    conn.row_factory = sqlite3.Row  # Para obtener diccionarios en lugar de tuplas
    return conn

# Crear tablas de la base de datos si no existen
def init_db():
    conn = get_db_connection()
    
    # Tabla de proyectos (como tu PRIMERA FASE en Excel)
    conn.execute('''
    CREATE TABLE IF NOT EXISTS proyectos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        tipo_actividad TEXT,
        tiene_inversion INTEGER DEFAULT 0,
        valor_inversion REAL DEFAULT 0,
        tasa_descuento REAL DEFAULT 0.001,
        nombre_producto TEXT,
        precio_producto REAL,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Tabla de costos (como tu SEGUNDA FASE - Costos)
    conn.execute('''
    CREATE TABLE IF NOT EXISTS costos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proyecto_id INTEGER,
        nombre TEXT NOT NULL,
        valor REAL NOT NULL,
        FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
    )
    ''')
    
    # Tabla de gastos (como tu SEGUNDA FASE - Gastos)
    conn.execute('''
    CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proyecto_id INTEGER,
        nombre TEXT NOT NULL,
        valor REAL NOT NULL,
        FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
    )
    ''')
    
    # Tabla de personal (como tu TERCERA FASE - Viabilidad Operativa)
    conn.execute('''
    CREATE TABLE IF NOT EXISTS personal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proyecto_id INTEGER,
        nombre TEXT NOT NULL,
        perfil TEXT,
        salario_mensual REAL NOT NULL,
        FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
    )
    ''')
    
    # Tabla de materiales (como tu Equipo y maquinaria)
    conn.execute('''
    CREATE TABLE IF NOT EXISTS materiales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proyecto_id INTEGER,
        nombre TEXT NOT NULL,
        valor REAL NOT NULL,
        FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
    )
    ''')
    
    # Tabla para ventas por día
    conn.execute('''
    CREATE TABLE IF NOT EXISTS ventas_dias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proyecto_id INTEGER,
        lunes INTEGER DEFAULT 0,
        martes INTEGER DEFAULT 0,
        miercoles INTEGER DEFAULT 0,
        jueves INTEGER DEFAULT 0,
        viernes INTEGER DEFAULT 0,
        sabado INTEGER DEFAULT 0,
        domingo INTEGER DEFAULT 0,
        FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
    )
    ''')
    
    # Tabla para ventas por semana
    conn.execute('''
    CREATE TABLE IF NOT EXISTS ventas_semanas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proyecto_id INTEGER,
        semana1 INTEGER DEFAULT 0,
        semana2 INTEGER DEFAULT 0,
        semana3 INTEGER DEFAULT 0,
        semana4 INTEGER DEFAULT 0,
        FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
    )
    ''')
    
    # Tabla para ventas por mes
    conn.execute('''
    CREATE TABLE IF NOT EXISTS ventas_meses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proyecto_id INTEGER,
        enero INTEGER DEFAULT 0,
        febrero INTEGER DEFAULT 0,
        marzo INTEGER DEFAULT 0,
        abril INTEGER DEFAULT 0,
        mayo INTEGER DEFAULT 0,
        junio INTEGER DEFAULT 0,
        julio INTEGER DEFAULT 0,
        FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
    )
    ''')
    
    # Tabla para ventas por año
    conn.execute('''
    CREATE TABLE IF NOT EXISTS ventas_anos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proyecto_id INTEGER,
        año1 INTEGER DEFAULT 0,
        año2 INTEGER DEFAULT 0,
        año3 INTEGER DEFAULT 0,
        año4 INTEGER DEFAULT 0,
        año5 INTEGER DEFAULT 0,
        año6 INTEGER DEFAULT 0,
        año7 INTEGER DEFAULT 0,
        FOREIGN KEY (proyecto_id) REFERENCES proyectos (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Llamar a init_db al iniciar la aplicación
with app.app_context():
    init_db()

# ==================== RUTAS PRINCIPALES ====================

@app.route('/')
def index():
    conn = get_db_connection()
    proyecto = conn.execute('SELECT * FROM proyectos ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()
    
    return render_template('index.html', proyecto=proyecto)

@app.route('/proyecto/datos-iniciales', methods=['GET', 'POST'])
def datos_iniciales():
    conn = get_db_connection()
    
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        tipo_actividad = request.form.get('tipo_actividad')
        tiene_inversion = 1 if request.form.get('tiene_inversion') == 'si' else 0
        valor_inversion = float(request.form.get('valor_inversion', 0))
        tasa_descuento = float(request.form.get('tasa_descuento', 0.001))
        nombre_producto = request.form.get('nombre_producto')
        precio_producto = float(request.form.get('precio_producto', 0))
        
        proyecto_existente = conn.execute('SELECT * FROM proyectos').fetchone()
        
        if proyecto_existente:
            conn.execute('''
                UPDATE proyectos SET 
                nombre = ?, tipo_actividad = ?, tiene_inversion = ?, 
                valor_inversion = ?, tasa_descuento = ?, nombre_producto = ?, 
                precio_producto = ?
                WHERE id = ?
            ''', (nombre, tipo_actividad, tiene_inversion, valor_inversion, 
                  tasa_descuento, nombre_producto, precio_producto, proyecto_existente['id']))
            flash('Proyecto actualizado correctamente', 'success')
        else:
            conn.execute('''
                INSERT INTO proyectos 
                (nombre, tipo_actividad, tiene_inversion, valor_inversion, 
                 tasa_descuento, nombre_producto, precio_producto)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (nombre, tipo_actividad, tiene_inversion, valor_inversion, 
                  tasa_descuento, nombre_producto, precio_producto))
            flash('Proyecto creado correctamente', 'success')
        
        conn.commit()
        conn.close()
        return redirect(url_for('datos_iniciales'))
    
    proyecto = conn.execute('SELECT * FROM proyectos ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()
    
    return render_template('proyecto/datos_iniciales.html', proyecto=proyecto)

# ==================== VIABILIDAD TÉCNICA ====================

@app.route('/proyecto/viabilidad-tecnica')
def viabilidad_tecnica():
    conn = get_db_connection()
    
    proyecto = conn.execute('SELECT * FROM proyectos ORDER BY id DESC LIMIT 1').fetchone()
    
    costos = []
    total_costos = 0
    if proyecto:
        costos = conn.execute('SELECT * FROM costos WHERE proyecto_id = ? ORDER BY id', 
                             (proyecto['id'],)).fetchall()
        total_costos_result = conn.execute('SELECT SUM(valor) as total FROM costos WHERE proyecto_id = ?', 
                                         (proyecto['id'],)).fetchone()
        total_costos = total_costos_result['total'] or 0 if total_costos_result else 0
    
    gastos = []
    total_gastos = 0
    if proyecto:
        gastos = conn.execute('SELECT * FROM gastos WHERE proyecto_id = ? ORDER BY id', 
                             (proyecto['id'],)).fetchall()
        total_gastos_result = conn.execute('SELECT SUM(valor) as total FROM gastos WHERE proyecto_id = ?', 
                                         (proyecto['id'],)).fetchone()
        total_gastos = total_gastos_result['total'] or 0 if total_gastos_result else 0
    
    conn.close()
    
    return render_template('proyecto/viabilidad_tecnica.html', 
                         proyecto=proyecto, 
                         costos=costos, 
                         gastos=gastos,
                         total_costos=total_costos,
                         total_gastos=total_gastos)

@app.route('/proyecto/agregar-costo', methods=['POST'])
def agregar_costo():
    if request.method == 'POST':
        nombre = request.form.get('nombre_costo')
        valor = float(request.form.get('valor_costo', 0))
        
        conn = get_db_connection()
        proyecto = conn.execute('SELECT * FROM proyectos ORDER BY id DESC LIMIT 1').fetchone()
        
        if proyecto:
            conn.execute('INSERT INTO costos (proyecto_id, nombre, valor) VALUES (?, ?, ?)',
                        (proyecto['id'], nombre, valor))
            conn.commit()
            flash(f'Costo "{nombre}" agregado correctamente', 'success')
        else:
            flash('Primero debes crear un proyecto', 'warning')
        
        conn.close()
    
    return redirect(url_for('viabilidad_tecnica'))

@app.route('/proyecto/editar-costo/<int:id>', methods=['GET', 'POST'])
def editar_costo(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        nombre = request.form.get('nombre_costo')
        valor = float(request.form.get('valor_costo', 0))
        
        conn.execute('UPDATE costos SET nombre = ?, valor = ? WHERE id = ?',
                    (nombre, valor, id))
        conn.commit()
        conn.close()
        
        flash(f'Costo actualizado correctamente', 'success')
        return redirect(url_for('viabilidad_tecnica'))
    
    costo = conn.execute('SELECT * FROM costos WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if not costo:
        flash('Costo no encontrado', 'error')
        return redirect(url_for('viabilidad_tecnica'))
    
    return render_template('componentes/modal_editar_costo.html', costo=costo)

@app.route('/proyecto/eliminar-costo/<int:id>')
def eliminar_costo(id):
    conn = get_db_connection()
    
    costo = conn.execute('SELECT * FROM costos WHERE id = ?', (id,)).fetchone()
    if costo:
        conn.execute('DELETE FROM costos WHERE id = ?', (id,))
        conn.commit()
        flash(f'Costo "{costo["nombre"]}" eliminado correctamente', 'success')
    
    conn.close()
    return redirect(url_for('viabilidad_tecnica'))

@app.route('/proyecto/agregar-gasto', methods=['POST'])
def agregar_gasto():
    if request.method == 'POST':
        nombre = request.form.get('nombre_gasto')
        valor = float(request.form.get('valor_gasto', 0))
        
        conn = get_db_connection()
        proyecto = conn.execute('SELECT * FROM proyectos ORDER BY id DESC LIMIT 1').fetchone()
        
        if proyecto:
            conn.execute('INSERT INTO gastos (proyecto_id, nombre, valor) VALUES (?, ?, ?)',
                        (proyecto['id'], nombre, valor))
            conn.commit()
            flash(f'Gasto "{nombre}" agregado correctamente', 'success')
        else:
            flash('Primero debes crear un proyecto', 'warning')
        
        conn.close()
    
    return redirect(url_for('viabilidad_tecnica'))

@app.route('/proyecto/editar-gasto/<int:id>', methods=['GET', 'POST'])
def editar_gasto(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        nombre = request.form.get('nombre_gasto')
        valor = float(request.form.get('valor_gasto', 0))
        
        conn.execute('UPDATE gastos SET nombre = ?, valor = ? WHERE id = ?',
                    (nombre, valor, id))
        conn.commit()
        conn.close()
        
        flash(f'Gasto actualizado correctamente', 'success')
        return redirect(url_for('viabilidad_tecnica'))
    
    gasto = conn.execute('SELECT * FROM gastos WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if not gasto:
        flash('Gasto no encontrado', 'error')
        return redirect(url_for('viabilidad_tecnica'))
    
    return render_template('componentes/modal_editar_gasto.html', gasto=gasto)

@app.route('/proyecto/eliminar-gasto/<int:id>')
def eliminar_gasto(id):
    conn = get_db_connection()
    
    gasto = conn.execute('SELECT * FROM gastos WHERE id = ?', (id,)).fetchone()
    if gasto:
        conn.execute('DELETE FROM gastos WHERE id = ?', (id,))
        conn.commit()
        flash(f'Gasto "{gasto["nombre"]}" eliminado correctamente', 'success')
    
    conn.close()
    return redirect(url_for('viabilidad_tecnica'))

# ==================== VIABILIDAD OPERATIVA ====================

@app.route('/proyecto/viabilidad-operativa')
def viabilidad_operativa():
    conn = get_db_connection()
    
    proyecto = conn.execute('SELECT * FROM proyectos ORDER BY id DESC LIMIT 1').fetchone()
    
    personal = []
    total_salarios = 0
    if proyecto:
        personal = conn.execute('SELECT * FROM personal WHERE proyecto_id = ? ORDER BY id', 
                               (proyecto['id'],)).fetchall()
        total_salarios_result = conn.execute('SELECT SUM(salario_mensual) as total FROM personal WHERE proyecto_id = ?', 
                                           (proyecto['id'],)).fetchone()
        total_salarios = total_salarios_result['total'] or 0 if total_salarios_result else 0
    
    total_costos = 0
    total_gastos = 0
    if proyecto:
        total_costos_result = conn.execute('SELECT SUM(valor) as total FROM costos WHERE proyecto_id = ?', 
                                         (proyecto['id'],)).fetchone()
        total_costos = total_costos_result['total'] or 0 if total_costos_result else 0
        
        total_gastos_result = conn.execute('SELECT SUM(valor) as total FROM gastos WHERE proyecto_id = ?', 
                                         (proyecto['id'],)).fetchone()
        total_gastos = total_gastos_result['total'] or 0 if total_gastos_result else 0
    
    conn.close()
    
    return render_template('proyecto/viabilidad_operativa.html', 
                         proyecto=proyecto, 
                         personal=personal,
                         total_salarios=total_salarios,
                         total_costos=total_costos,
                         total_gastos=total_gastos)

@app.route('/proyecto/agregar-personal', methods=['POST'])
def agregar_personal():
    if request.method == 'POST':
        nombre = request.form.get('nombre_personal')
        perfil = request.form.get('perfil_personal')
        salario_mensual = float(request.form.get('salario_mensual', 0))
        
        conn = get_db_connection()
        proyecto = conn.execute('SELECT * FROM proyectos ORDER BY id DESC LIMIT 1').fetchone()
        
        if proyecto:
            conn.execute('INSERT INTO personal (proyecto_id, nombre, perfil, salario_mensual) VALUES (?, ?, ?, ?)',
                        (proyecto['id'], nombre, perfil, salario_mensual))
            conn.commit()
            flash(f'Personal "{nombre}" agregado correctamente', 'success')
        else:
            flash('Primero debes crear un proyecto', 'warning')
        
        conn.close()
    
    return redirect(url_for('viabilidad_operativa'))

@app.route('/proyecto/editar-personal/<int:id>', methods=['GET', 'POST'])
def editar_personal(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        nombre = request.form.get('nombre_personal')
        perfil = request.form.get('perfil_personal')
        salario_mensual = float(request.form.get('salario_mensual', 0))
        
        conn.execute('UPDATE personal SET nombre = ?, perfil = ?, salario_mensual = ? WHERE id = ?',
                    (nombre, perfil, salario_mensual, id))
        conn.commit()
        conn.close()
        
        flash(f'Personal actualizado correctamente', 'success')
        return redirect(url_for('viabilidad_operativa'))
    
    persona = conn.execute('SELECT * FROM personal WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if not persona:
        flash('Personal no encontrado', 'error')
        return redirect(url_for('viabilidad_operativa'))
    
    return render_template('componentes/modal_editar_personal.html', persona=persona)

@app.route('/proyecto/eliminar-personal/<int:id>')
def eliminar_personal(id):
    conn = get_db_connection()
    
    persona = conn.execute('SELECT * FROM personal WHERE id = ?', (id,)).fetchone()
    if persona:
        conn.execute('DELETE FROM personal WHERE id = ?', (id,))
        conn.commit()
        flash(f'Personal "{persona["nombre"]}" eliminado correctamente', 'success')
    
    conn.close()
    return redirect(url_for('viabilidad_operativa'))

# ==================== EQUIPO Y MAQUINARIA ====================

@app.route('/proyecto/equipo-maquinaria')
def equipo_maquinaria():
    conn = get_db_connection()
    
    proyecto = conn.execute('SELECT * FROM proyectos ORDER BY id DESC LIMIT 1').fetchone()
    
    materiales = []
    total_materiales = 0
    if proyecto:
        materiales = conn.execute('SELECT * FROM materiales WHERE proyecto_id = ? ORDER BY id', 
                                 (proyecto['id'],)).fetchall()
        total_materiales_result = conn.execute('SELECT SUM(valor) as total FROM materiales WHERE proyecto_id = ?', 
                                             (proyecto['id'],)).fetchone()
        total_materiales = total_materiales_result['total'] or 0 if total_materiales_result else 0
    
    total_costos = 0
    total_gastos = 0
    total_salarios = 0
    if proyecto:
        total_costos_result = conn.execute('SELECT SUM(valor) as total FROM costos WHERE proyecto_id = ?', 
                                         (proyecto['id'],)).fetchone()
        total_costos = total_costos_result['total'] or 0 if total_costos_result else 0
        
        total_gastos_result = conn.execute('SELECT SUM(valor) as total FROM gastos WHERE proyecto_id = ?', 
                                         (proyecto['id'],)).fetchone()
        total_gastos = total_gastos_result['total'] or 0 if total_gastos_result else 0
        
        total_salarios_result = conn.execute('SELECT SUM(salario_mensual) as total FROM personal WHERE proyecto_id = ?', 
                                           (proyecto['id'],)).fetchone()
        total_salarios = total_salarios_result['total'] or 0 if total_salarios_result else 0
    
    conn.close()
    
    return render_template('proyecto/equipo_maquinaria.html', 
                         proyecto=proyecto, 
                         materiales=materiales,
                         total_materiales=total_materiales,
                         total_costos=total_costos,
                         total_gastos=total_gastos,
                         total_salarios=total_salarios)

@app.route('/proyecto/agregar-material', methods=['POST'])
def agregar_material():
    if request.method == 'POST':
        nombre = request.form.get('nombre_material')
        valor = float(request.form.get('valor_material', 0))
        
        conn = get_db_connection()
        proyecto = conn.execute('SELECT * FROM proyectos ORDER BY id DESC LIMIT 1').fetchone()
        
        if proyecto:
            conn.execute('INSERT INTO materiales (proyecto_id, nombre, valor) VALUES (?, ?, ?)',
                        (proyecto['id'], nombre, valor))
            conn.commit()
            flash(f'Material "{nombre}" agregado correctamente', 'success')
        else:
            flash('Primero debes crear un proyecto', 'warning')
        
        conn.close()
    
    return redirect(url_for('equipo_maquinaria'))

@app.route('/proyecto/editar-material/<int:id>', methods=['GET', 'POST'])
def editar_material(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        nombre = request.form.get('nombre_material')
        valor = float(request.form.get('valor_material', 0))
        
        conn.execute('UPDATE materiales SET nombre = ?, valor = ? WHERE id = ?',
                    (nombre, valor, id))
        conn.commit()
        conn.close()
        
        flash(f'Material actualizado correctamente', 'success')
        return redirect(url_for('equipo_maquinaria'))
    
    material = conn.execute('SELECT * FROM materiales WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if not material:
        flash('Material no encontrado', 'error')
        return redirect(url_for('equipo_maquinaria'))
    
    return render_template('componentes/modal_editar_material.html', material=material)

@app.route('/proyecto/eliminar-material/<int:id>')
def eliminar_material(id):
    conn = get_db_connection()
    
    material = conn.execute('SELECT * FROM materiales WHERE id = ?', (id,)).fetchone()
    if material:
        conn.execute('DELETE FROM materiales WHERE id = ?', (id,))
        conn.commit()
        flash(f'Material "{material["nombre"]}" eliminado correctamente', 'success')
    
    conn.close()
    return redirect(url_for('equipo_maquinaria'))

# ==================== FLUJOS DE CAJA ====================

@app.route('/proyecto/flujos-caja')
def flujos_caja():
    conn = get_db_connection()
    
    proyecto = conn.execute('SELECT * FROM proyectos ORDER BY id DESC LIMIT 1').fetchone()
    
    totales = {
        'costos': 0,
        'gastos': 0,
        'salarios': 0,
        'materiales': 0
    }
    
    ventas_dias = None
    ventas_semanas = None
    ventas_meses = None
    ventas_anos = None
    
    if proyecto:
        # Costos
        total_costos_result = conn.execute('SELECT SUM(valor) as total FROM costos WHERE proyecto_id = ?', 
                                         (proyecto['id'],)).fetchone()
        totales['costos'] = total_costos_result['total'] or 0 if total_costos_result else 0
        
        # Gastos
        total_gastos_result = conn.execute('SELECT SUM(valor) as total FROM gastos WHERE proyecto_id = ?', 
                                         (proyecto['id'],)).fetchone()
        totales['gastos'] = total_gastos_result['total'] or 0 if total_gastos_result else 0
        
        # Personal
        total_salarios_result = conn.execute('SELECT SUM(salario_mensual) as total FROM personal WHERE proyecto_id = ?', 
                                           (proyecto['id'],)).fetchone()
        totales['salarios'] = total_salarios_result['total'] or 0 if total_salarios_result else 0
        
        # Materiales
        total_materiales_result = conn.execute('SELECT SUM(valor) as total FROM materiales WHERE proyecto_id = ?', 
                                             (proyecto['id'],)).fetchone()
        totales['materiales'] = total_materiales_result['total'] or 0 if total_materiales_result else 0
        
        # Obtener ventas
        ventas_dias = conn.execute('SELECT * FROM ventas_dias WHERE proyecto_id = ?', 
                                  (proyecto['id'],)).fetchone()
        ventas_semanas = conn.execute('SELECT * FROM ventas_semanas WHERE proyecto_id = ?', 
                                     (proyecto['id'],)).fetchone()
        ventas_meses = conn.execute('SELECT * FROM ventas_meses WHERE proyecto_id = ?', 
                                   (proyecto['id'],)).fetchone()
        ventas_anos = conn.execute('SELECT * FROM ventas_anos WHERE proyecto_id = ?', 
                                  (proyecto['id'],)).fetchone()
    
    conn.close()
    
    return render_template('proyecto/flujos_caja.html', 
                         proyecto=proyecto,
                         totales=totales,
                         ventas_dias=ventas_dias,
                         ventas_semanas=ventas_semanas,
                         ventas_meses=ventas_meses,
                         ventas_anos=ventas_anos)

@app.route('/proyecto/guardar-ventas-dias', methods=['POST'])
def guardar_ventas_dias():
    conn = get_db_connection()
    proyecto = conn.execute('SELECT * FROM proyectos ORDER BY id DESC LIMIT 1').fetchone()
    
    if not proyecto:
        flash('Primero debes crear un proyecto', 'warning')
        conn.close()
        return redirect(url_for('flujos_caja'))
    
    datos = {
        'lunes': int(request.form.get('lunes', 0)),
        'martes': int(request.form.get('martes', 0)),
        'miercoles': int(request.form.get('miercoles', 0)),
        'jueves': int(request.form.get('jueves', 0)),
        'viernes': int(request.form.get('viernes', 0)),
        'sabado': int(request.form.get('sabado', 0)),
        'domingo': int(request.form.get('domingo', 0))
    }
    
    existente = conn.execute('SELECT * FROM ventas_dias WHERE proyecto_id = ?', 
                            (proyecto['id'],)).fetchone()
    
    if existente:
        conn.execute('''
            UPDATE ventas_dias SET 
            lunes = ?, martes = ?, miercoles = ?, jueves = ?, 
            viernes = ?, sabado = ?, domingo = ?
            WHERE proyecto_id = ?
        ''', (datos['lunes'], datos['martes'], datos['miercoles'], datos['jueves'],
              datos['viernes'], datos['sabado'], datos['domingo'], proyecto['id']))
    else:
        conn.execute('''
            INSERT INTO ventas_dias 
            (proyecto_id, lunes, martes, miercoles, jueves, viernes, sabado, domingo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (proyecto['id'], datos['lunes'], datos['martes'], datos['miercoles'], 
              datos['jueves'], datos['viernes'], datos['sabado'], datos['domingo']))
    
    conn.commit()
    conn.close()
    
    flash('Ventas por día guardadas correctamente', 'success')
    return redirect(url_for('flujos_caja'))

@app.route('/proyecto/guardar-ventas-semanas', methods=['POST'])
def guardar_ventas_semanas():
    conn = get_db_connection()
    proyecto = conn.execute('SELECT * FROM proyectos ORDER BY id DESC LIMIT 1').fetchone()
    
    if not proyecto:
        flash('Primero debes crear un proyecto', 'warning')
        conn.close()
        return redirect(url_for('flujos_caja'))
    
    datos = {
        'semana1': int(request.form.get('semana1', 0)),
        'semana2': int(request.form.get('semana2', 0)),
        'semana3': int(request.form.get('semana3', 0)),
        'semana4': int(request.form.get('semana4', 0))
    }
    
    existente = conn.execute('SELECT * FROM ventas_semanas WHERE proyecto_id = ?', 
                            (proyecto['id'],)).fetchone()
    
    if existente:
        conn.execute('''
            UPDATE ventas_semanas SET 
            semana1 = ?, semana2 = ?, semana3 = ?, semana4 = ?
            WHERE proyecto_id = ?
        ''', (datos['semana1'], datos['semana2'], datos['semana3'], 
              datos['semana4'], proyecto['id']))
    else:
        conn.execute('''
            INSERT INTO ventas_semanas 
            (proyecto_id, semana1, semana2, semana3, semana4)
            VALUES (?, ?, ?, ?, ?)
        ''', (proyecto['id'], datos['semana1'], datos['semana2'], 
              datos['semana3'], datos['semana4']))
    
    conn.commit()
    conn.close()
    
    flash('Ventas por semana guardadas correctamente', 'success')
    return redirect(url_for('flujos_caja'))

@app.route('/proyecto/guardar-ventas-meses', methods=['POST'])
def guardar_ventas_meses():
    conn = get_db_connection()
    proyecto = conn.execute('SELECT * FROM proyectos ORDER BY id DESC LIMIT 1').fetchone()
    
    if not proyecto:
        flash('Primero debes crear un proyecto', 'warning')
        conn.close()
        return redirect(url_for('flujos_caja'))
    
    datos = {
        'enero': int(request.form.get('enero', 0)),
        'febrero': int(request.form.get('febrero', 0)),
        'marzo': int(request.form.get('marzo', 0)),
        'abril': int(request.form.get('abril', 0)),
        'mayo': int(request.form.get('mayo', 0)),
        'junio': int(request.form.get('junio', 0)),
        'julio': int(request.form.get('julio', 0))
    }
    
    existente = conn.execute('SELECT * FROM ventas_meses WHERE proyecto_id = ?', 
                            (proyecto['id'],)).fetchone()
    
    if existente:
        conn.execute('''
            UPDATE ventas_meses SET 
            enero = ?, febrero = ?, marzo = ?, abril = ?, 
            mayo = ?, junio = ?, julio = ?
            WHERE proyecto_id = ?
        ''', (datos['enero'], datos['febrero'], datos['marzo'], datos['abril'],
              datos['mayo'], datos['junio'], datos['julio'], proyecto['id']))
    else:
        conn.execute('''
            INSERT INTO ventas_meses 
            (proyecto_id, enero, febrero, marzo, abril, mayo, junio, julio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (proyecto['id'], datos['enero'], datos['febrero'], datos['marzo'], 
              datos['abril'], datos['mayo'], datos['junio'], datos['julio']))
    
    conn.commit()
    conn.close()
    
    flash('Ventas por mes guardadas correctamente', 'success')
    return redirect(url_for('flujos_caja'))

@app.route('/proyecto/guardar-ventas-anos', methods=['POST'])
def guardar_ventas_anos():
    conn = get_db_connection()
    proyecto = conn.execute('SELECT * FROM proyectos ORDER BY id DESC LIMIT 1').fetchone()
    
    if not proyecto:
        flash('Primero debes crear un proyecto', 'warning')
        conn.close()
        return redirect(url_for('flujos_caja'))
    
    datos = {
        'año1': int(request.form.get('año1', 0)),
        'año2': int(request.form.get('año2', 0)),
        'año3': int(request.form.get('año3', 0)),
        'año4': int(request.form.get('año4', 0)),
        'año5': int(request.form.get('año5', 0)),
        'año6': int(request.form.get('año6', 0)),
        'año7': int(request.form.get('año7', 0))
    }
    
    existente = conn.execute('SELECT * FROM ventas_anos WHERE proyecto_id = ?', 
                            (proyecto['id'],)).fetchone()
    
    if existente:
        conn.execute('''
            UPDATE ventas_anos SET 
            año1 = ?, año2 = ?, año3 = ?, año4 = ?, 
            año5 = ?, año6 = ?, año7 = ?
            WHERE proyecto_id = ?
        ''', (datos['año1'], datos['año2'], datos['año3'], datos['año4'],
              datos['año5'], datos['año6'], datos['año7'], proyecto['id']))
    else:
        conn.execute('''
            INSERT INTO ventas_anos 
            (proyecto_id, año1, año2, año3, año4, año5, año6, año7)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (proyecto['id'], datos['año1'], datos['año2'], datos['año3'], 
              datos['año4'], datos['año5'], datos['año6'], datos['año7']))
    
    conn.commit()
    conn.close()
    
    flash('Ventas por año guardadas correctamente', 'success')
    return redirect(url_for('flujos_caja'))

# ==================== FUNCIONES DE CÁLCULO ====================

def calcular_van(tasa_descuento, flujos):
    """Calcula el VAN dado una tasa de descuento y una lista de flujos."""
    van = 0
    for i, flujo in enumerate(flujos):
        van += flujo / ((1 + tasa_descuento) ** i)
    return van

def calcular_tir(flujos, iteraciones=1000, precision=0.0001):
    """Calcula la TIR usando el método de bisección."""
    def van_con_tasa(tasa):
        total = 0
        for i, flujo in enumerate(flujos):
            total += flujo / ((1 + tasa) ** i)
        return total
    
    tasa_min = -0.99
    tasa_max = 10.0
    
    van_min = van_con_tasa(tasa_min)
    van_max = van_con_tasa(tasa_max)
    
    if van_min * van_max > 0:
        return None
    
    for _ in range(iteraciones):
        tasa_media = (tasa_min + tasa_max) / 2
        van_media = van_con_tasa(tasa_media)
        
        if abs(van_media) < precision:
            return tasa_media
        
        if van_min * van_media < 0:
            tasa_max = tasa_media
            van_max = van_media
        else:
            tasa_min = tasa_media
            van_min = van_media
    
    return (tasa_min + tasa_max) / 2

def calcular_bc(flujos, tasa_descuento):
    """Calcula la relación Beneficio/Costo."""
    beneficios_pv = 0
    costos_pv = 0
    
    for i, flujo in enumerate(flujos):
        if flujo > 0:
            beneficios_pv += flujo / ((1 + tasa_descuento) ** i)
        else:
            costos_pv += abs(flujo) / ((1 + tasa_descuento) ** i)
    
    if costos_pv == 0:
        return float('inf')
    
    return beneficios_pv / costos_pv

def calcular_pri(flujos):
    """Calcula el Periodo de Recuperación de la Inversión."""
    inversion_inicial = abs(flujos[0]) if flujos and flujos[0] < 0 else 0
    if inversion_inicial == 0:
        return 0
    
    acumulado = 0
    
    for i, flujo in enumerate(flujos):
        if i == 0:
            continue
        
        acumulado += flujo
        
        if acumulado >= inversion_inicial:
            flujo_anterior = flujos[i-1] if i > 1 else 0
            faltante_antes = inversion_inicial - (acumulado - flujo)
            proporcion = faltante_antes / flujo if flujo != 0 else 0
            
            return (i - 1) + proporcion
    
    return None

# Función helper para plantillas
def calcular_van_template(tasa, flujos):
    """Versión para usar en plantillas Jinja2"""
    return calcular_van(tasa, flujos)

@app.context_processor
def utility_processor():
    """Inyecta funciones en todas las plantillas"""
    return dict(calcular_van=calcular_van_template)

# ==================== CÁLCULOS FINANCIEROS ====================

@app.route('/resultados/calculos-financieros')
def calculos_financieros():
    conn = get_db_connection()
    
    proyecto = conn.execute('SELECT * FROM proyectos ORDER BY id DESC LIMIT 1').fetchone()
    
    if not proyecto:
        flash('Primero debes crear un proyecto', 'warning')
        conn.close()
        return redirect(url_for('index'))
    
    resultados = {
        'proyecto': proyecto,
        'totales': {},
        'calculos': {}
    }
    
    # Obtener totales
    # Costos
    total_costos_result = conn.execute('SELECT SUM(valor) as total FROM costos WHERE proyecto_id = ?', 
                                     (proyecto['id'],)).fetchone()
    resultados['totales']['costos'] = total_costos_result['total'] or 0 if total_costos_result else 0
    
    # Gastos
    total_gastos_result = conn.execute('SELECT SUM(valor) as total FROM gastos WHERE proyecto_id = ?', 
                                     (proyecto['id'],)).fetchone()
    resultados['totales']['gastos'] = total_gastos_result['total'] or 0 if total_gastos_result else 0
    
    # Personal
    total_salarios_result = conn.execute('SELECT SUM(salario_mensual) as total FROM personal WHERE proyecto_id = ?', 
                                       (proyecto['id'],)).fetchone()
    resultados['totales']['salarios'] = total_salarios_result['total'] or 0 if total_salarios_result else 0
    
    # Materiales
    total_materiales_result = conn.execute('SELECT SUM(valor) as total FROM materiales WHERE proyecto_id = ?', 
                                         (proyecto['id'],)).fetchone()
    resultados['totales']['materiales'] = total_materiales_result['total'] or 0 if total_materiales_result else 0
    
    # Inversión inicial
    inversion_inicial = proyecto['valor_inversion'] if proyecto['tiene_inversion'] == 1 else 0
    
    # Obtener ventas por año para flujos
    ventas_anos = conn.execute('SELECT * FROM ventas_anos WHERE proyecto_id = ?', 
                              (proyecto['id'],)).fetchone()
    
    conn.close()
    
    # Construir flujos de caja para 7 años
    flujos_anuales = []
    
    # Año 0: Inversión inicial (negativa)
    flujos_anuales.append(-inversion_inicial)
    
    # Años 1-7: Flujos netos
    if ventas_anos:
        # Calcular ingresos anuales usando get()
        for i in range(1, 8):
            ventas_key = f'año{i}'
            # Usar get() en lugar de getattr para mayor seguridad
            ventas = ventas_anos[ventas_key] if ventas_key in ventas_anos.keys() else 0
            ingresos_anuales = ventas * proyecto['precio_producto']
            
            # Calcular flujo neto
            costo_anual = resultados['totales']['costos'] / 7 if resultados['totales']['costos'] > 0 else 0
            gasto_anual = resultados['totales']['gastos'] / 7 if resultados['totales']['gastos'] > 0 else 0
            salario_anual = resultados['totales']['salarios'] * 12 if resultados['totales']['salarios'] > 0 else 0
            
            flujo_neto = ingresos_anuales - costo_anual - gasto_anual - salario_anual
            flujos_anuales.append(flujo_neto)
    else:
        # Valores por defecto si no hay ventas registradas
        for i in range(7):
            flujos_anuales.append(0)
    
    # Realizar cálculos financieros
    tasa_descuento = proyecto['tasa_descuento']
    
    try:
        # VAN
        van = calcular_van(tasa_descuento, flujos_anuales)
        resultados['calculos']['van'] = van
        
        # TIR
        tir = calcular_tir(flujos_anuales)
        resultados['calculos']['tir'] = tir * 100 if tir else 0
        
        # B/C
        bc = calcular_bc(flujos_anuales, tasa_descuento)
        resultados['calculos']['bc'] = bc
        
        # PRI
        pri = calcular_pri(flujos_anuales)
        resultados['calculos']['pri'] = pri
        
        # Otros indicadores
        resultados['calculos']['flujos'] = flujos_anuales
        resultados['calculos']['inversion_total'] = (
            inversion_inicial + 
            resultados['totales']['costos'] + 
            resultados['totales']['gastos'] + 
            (resultados['totales']['salarios'] * 12 * 7) +  # 7 años de salarios
            resultados['totales']['materiales']
        )
        
        # Rentabilidad
        if inversion_inicial > 0:
            resultados['calculos']['rentabilidad'] = (van / inversion_inicial) * 100
        else:
            resultados['calculos']['rentabilidad'] = 0
            
    except Exception as e:
        resultados['calculos']['error'] = f"Error en cálculos: {str(e)}"
        resultados['calculos']['van'] = 0
        resultados['calculos']['tir'] = 0
        resultados['calculos']['bc'] = 0
        resultados['calculos']['pri'] = 0
        resultados['calculos']['flujos'] = flujos_anuales
        resultados['calculos']['inversion_total'] = 0
        resultados['calculos']['rentabilidad'] = 0
    
    return render_template('resultados/calculo_financiero.html', resultados=resultados)

# Ruta para limpiar todos los datos
@app.route('/limpiar-datos')
def limpiar_datos():
    conn = get_db_connection()
    
    conn.execute('DELETE FROM costos')
    conn.execute('DELETE FROM gastos')
    conn.execute('DELETE FROM personal')
    conn.execute('DELETE FROM materiales')
    conn.execute('DELETE FROM ventas_dias')
    conn.execute('DELETE FROM ventas_semanas')
    conn.execute('DELETE FROM ventas_meses')
    conn.execute('DELETE FROM ventas_anos')
    
    conn.commit()
    conn.close()
    
    flash('Todos los datos han sido limpiados (excepto el proyecto)', 'warning')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)