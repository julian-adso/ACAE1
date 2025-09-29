from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from app.models.decorators import login_required
from app.models.ingreso import Ingreso
from ..models.salida import Salida
from .. import db
from app.models.user import User
from app.models.admin import Admin
from app.models.login import Login
from datetime import date, datetime, timedelta
import hashlib
from collections import defaultdict
from app.models.super import Super
from calendar import monthrange
from flask import send_file
from app.utilidad.utils_excel import exportar_asistencia_excel

user_bp = Blueprint('user', __name__)

def registrar_ausencias_global():

    hoy = datetime.now()
    
    # --- Rango del mes actual ---
    primer_dia = hoy.replace(day=1)
    ultimo_dia = hoy.replace(day=monthrange(hoy.year, hoy.month)[1])
    dias_mes = [primer_dia.replace(day=d) for d in range(1, ultimo_dia.day + 1)]
    
    # --- Usuarios ---
    usuarios = User.query.all()
    for usuario in usuarios:
        fechas_con_ingreso = set(
            i.fecha for i in Ingreso.query.filter_by(user_id=usuario.idUser)
            .filter(db.extract('month', Ingreso.fecha) == hoy.month)
            .all()
        )
        for dia in dias_mes:
            if dia.date() < hoy.date() and dia.date() not in fechas_con_ingreso:
                if not Ingreso.query.filter_by(user_id=usuario.idUser, fecha=dia.date()).first():
                    ausencia = Ingreso(
                        user_id=usuario.idUser,
                        admin_id=None,
                        rol='User',
                        fecha=dia.date(),
                        hora=datetime.strptime("00:00", "%H:%M").time(),
                        horario=usuario.horario,
                        estado='Ausente',
                        motivo='No asistió'
                    )
                    db.session.add(ausencia)

    # --- Admins ---
    admins = Admin.query.all()
    for admin in admins:
        fechas_con_ingreso = set(
            i.fecha for i in Ingreso.query.filter_by(admin_id=admin.idAdmin)
            .filter(db.extract('month', Ingreso.fecha) == hoy.month)
            .all()
        )
        for dia in dias_mes:
            if dia.date() < hoy.date() and dia.date() not in fechas_con_ingreso:
                if not Ingreso.query.filter_by(admin_id=admin.idAdmin, fecha=dia.date()).first():
                    ausencia = Ingreso(
                        user_id=None,
                        admin_id=admin.idAdmin,
                        rol='Admin',
                        fecha=dia.date(),
                        hora=datetime.strptime("00:00", "%H:%M").time(),
                        horario=admin.horario,
                        estado='Ausente',
                        motivo='No asistió'
                    )
                    db.session.add(ausencia)

    db.session.commit()

# Página inicial (ahora inicio.html)
@user_bp.route('/')
def home():
    return render_template('inicio.html')

# Login route
@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Hashear la contraseña ingresada (SHA1)
        hashed_password = hashlib.sha1(password.encode()).hexdigest()
        
        # Buscar en tabla Login
        login = Login.query.filter_by(usernameLogin=username, passwordLogin=hashed_password).first()

        if login:
            # Verificar si corresponde a un User
            user = User.query.filter_by(login_id=login.idLogin).first()
            if user:
                session['user_id'] = user.idUser
                session['username'] = user.usernameUser
                session['role'] = 'user'
                return redirect(url_for('user.index'))  # Página de usuarios (index.html)

            # Verificar si corresponde a un Admin
            admin = Admin.query.filter_by(login_id=login.idLogin).first()
            if admin:
                session['admin_id'] = admin.idAdmin
                session['username'] = login.usernameLogin
                session['role'] = 'admin'
                return redirect(url_for('user.dashboard'))  # Página de admins

            # Verificar si corresponde a un Super
            super_user = Super.query.filter_by(login_id=login.idLogin).first()
            if super_user:
                session['super_id'] = super_user.idSuper
                session['username'] = super_user.usernameSuper
                session['role'] = 'super'
                return redirect(url_for('user.home_super'))  # Página de super

        # Si no encontró nada
        flash('Usuario o contraseña incorrectos')
        return render_template('login.html')

    return render_template('login.html')

# Registro de empleados (solo admin)
@user_bp.route('/register', methods=['GET', 'POST'])
@login_required(role='admin')
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        document = request.form.get('document')
        phone = request.form.get('phone')
        email = request.form.get('email')
        horario = request.form.get('horario')

        if not all([username, password, document, phone, email, horario]):
            flash('Todos los campos son obligatorios')
            return render_template('register.html')

        if User.query.filter_by(usernameUser=username).first():
            flash('El usuario ya existe')
            return render_template('register.html')

        # Crear Login
        login = Login(usernameLogin=username)
        login.set_password(password)
        db.session.add(login)
        db.session.flush()

        # Crear User
        user = User(
            login_id=login.idLogin,
            usernameUser=username,
            passwordUser=login.passwordLogin,
            documentUser=document,
            phoneUser=phone,
            emailUser=email,
            horario=horario
        )
        db.session.add(user)
        db.session.commit()

        flash('Empleado registrado exitosamente')
        return redirect(url_for('user.dashboard'))

    return render_template('register.html')

@user_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('user.home'))

@user_bp.route('/index')
def index():
    if 'user_id' not in session:
        return redirect(url_for('user.login'))

    usuario = User.query.get(session['user_id'])
    hoy = datetime.now()

    # --- REGISTRAR AUSENCIAS AUTOMÁTICAMENTE ---
    from calendar import monthrange
    primer_dia = hoy.replace(day=1)
    ultimo_dia = hoy.replace(day=monthrange(hoy.year, hoy.month)[1])

    # Obtener todos los días del mes actual
    dias_mes = [primer_dia.replace(day=d) for d in range(1, ultimo_dia.day + 1)]

    # Obtener fechas con ingreso registrado
    fechas_con_ingreso = set(
        i.fecha for i in Ingreso.query.filter_by(user_id=usuario.idUser)
        .filter(db.extract('month', Ingreso.fecha) == hoy.month)
        .all()
    )

    # Registrar ausencia para los días sin ingreso y que sean <= hoy
    for dia in dias_mes:
         if dia.date() < hoy.date() and dia.date() not in fechas_con_ingreso:
            if not Ingreso.query.filter_by(user_id=usuario.idUser, fecha=dia.date()).first():
                ausencia = Ingreso(
                    user_id=usuario.idUser,
                    admin_id=None,
                    rol='User',  # <--- Asigna el rol correspondiente
                    fecha=dia.date(),
                    hora=datetime.strptime("00:00", "%H:%M").time(),
                    horario=usuario.horario,
                    estado='Ausente',
                    motivo='No asistió'
                )
                db.session.add(ausencia)
    db.session.commit()
    # --- FIN REGISTRO AUTOMÁTICO ---

    asistencias = Ingreso.query.filter_by(user_id=usuario.idUser, estado='Presente')\
                               .filter(db.extract('month', Ingreso.fecha) == hoy.month).count()

    ausencias = Ingreso.query.filter_by(user_id=usuario.idUser, estado='Ausente')\
                             .filter(db.extract('month', Ingreso.fecha) == hoy.month).count()

    historial = Ingreso.query.filter_by(user_id=usuario.idUser)\
                             .order_by(Ingreso.fecha.desc(), Ingreso.hora.desc())\
                             .limit(10).all()

    return render_template(
        'index.html',
        username=usuario.usernameUser,
        asistencias=asistencias,
        ausencias=ausencias,
        historial=historial
    )

@user_bp.route('/dashboard')
def dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('user.login'))

    return render_template('dashboard.html', username=session['username'])

# Registrar el horario y el ingreso
def determinar_horario_actual():
    ahora = datetime.now().time()

    if ahora >= datetime.strptime("06:00", "%H:%M").time() and ahora < datetime.strptime("12:00", "%H:%M").time():
        return "Mañana"
    elif ahora >= datetime.strptime("12:00", "%H:%M").time() and ahora < datetime.strptime("18:00", "%H:%M").time():
        return "Tarde"
    else:
        return "Noche"
    
# route del super

@user_bp.route('/home_super')
def home_super():
    if 'super_id' not in session:
        return redirect(url_for('user.login'))
    return render_template('home.html', username=session['username'])


@user_bp.route('/registrar_ingreso', methods=['POST'])
def registrar_ingreso():
    data = request.get_json()
    documento = data.get('documento')
    motivo = data.get('motivo')

    if not documento:
        return jsonify({'success': False, 'message': 'Documento requerido'}), 400

    # 1. Buscar si es Usuario
    usuario = User.query.filter_by(documentUser=documento).first()
    if usuario:
        horario_actual = determinar_horario_actual()
        horario_trabajador = usuario.horario

        ingreso = Ingreso.query.filter_by(user_id=usuario.idUser, fecha=date.today()).order_by(Ingreso.idIngreso.desc()).first()

        if ingreso:
            salida = Salida.query.filter_by(user_id=usuario.idUser, ingreso_id=ingreso.idIngreso).first()
            if salida:
                if not motivo:
                    return jsonify({'success': False, 'message': 'Debe ingresar un motivo para volver a entrar.'}), 400

                nuevo_ingreso = Ingreso(
                    user_id=usuario.idUser,
                    admin_id=None,
                    rol="User",
                    fecha=date.today(),
                    hora=datetime.now().time(),
                    horario=horario_actual,
                    estado='Presente',
                    motivo=motivo
                )
                db.session.add(nuevo_ingreso)
                db.session.commit()
                return jsonify({'success': True, 'message': f'Nuevo ingreso registrado con motivo: {motivo}'})
            else:
                nueva_salida = Salida(
                    user_id=usuario.idUser,
                    admin_id=None,
                    rol="User",
                    ingreso_id=ingreso.idIngreso,
                    fecha=date.today(),
                    hora_salida=datetime.now().time(),
                    horario=ingreso.horario
                )
                db.session.add(nueva_salida)
                db.session.commit()
                return jsonify({'success': True, 'message': 'Salida registrada'})
        else:
            if horario_actual != horario_trabajador and not motivo:
                return jsonify({'success': False, 'message': f'El horario actual es {horario_actual}, pero su horario asignado es {horario_trabajador}. Ingrese un motivo para continuar.'}), 400

            nuevo_ingreso = Ingreso(
                user_id=usuario.idUser,
                admin_id=None,
                rol="User",
                fecha=date.today(),
                hora=datetime.now().time(),
                horario=horario_actual,
                estado='Presente',
                motivo=motivo
            )
            db.session.add(nuevo_ingreso)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Ingreso registrado'})

    # 2. Buscar si es Admin
    admin = Admin.query.filter_by(documentAdmin=documento).first()
    if admin:
        horario_actual = determinar_horario_actual()
        horario_admin = admin.horario

        ingreso = Ingreso.query.filter_by(admin_id=admin.idAdmin, fecha=date.today()).order_by(Ingreso.idIngreso.desc()).first()

        if ingreso:
            salida = Salida.query.filter_by(admin_id=admin.idAdmin, ingreso_id=ingreso.idIngreso).first()
            if salida:
                if not motivo:
                    return jsonify({'success': False, 'message': 'Debe ingresar un motivo para volver a entrar (Admin).'}), 400

                nuevo_ingreso = Ingreso(
                    user_id=None,
                    admin_id=admin.idAdmin,
                    rol="Admin",
                    fecha=date.today(),
                    hora=datetime.now().time(),
                    horario=horario_actual,
                    estado='Presente',
                    motivo=motivo
                )
                db.session.add(nuevo_ingreso)
                db.session.commit()
                return jsonify({'success': True, 'message': f'Nuevo ingreso (Admin) registrado con motivo: {motivo}'})
            else:
                nueva_salida = Salida(
                    user_id=None,
                    admin_id=admin.idAdmin,
                    rol="Admin",
                    ingreso_id=ingreso.idIngreso,
                    fecha=date.today(),
                    hora_salida=datetime.now().time(),
                    horario=ingreso.horario
                )
                db.session.add(nueva_salida)
                db.session.commit()
                return jsonify({'success': True, 'message': 'Salida (Admin) registrada'})
        else:
            if horario_actual != horario_admin and not motivo:
                return jsonify({'success': False, 'message': f'El horario actual es {horario_actual}, pero su horario asignado es {horario_admin}. Ingrese un motivo para continuar.'}), 400

            nuevo_ingreso = Ingreso(
                user_id=None,
                admin_id=admin.idAdmin,
                rol="Admin",
                fecha=date.today(),
                hora=datetime.now().time(),
                horario=horario_actual,
                estado='Presente',
                motivo=motivo
            )
            db.session.add(nuevo_ingreso)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Ingreso (Admin) registrado'})

    # 3. Si no se encontró nada
    return jsonify({'success': False, 'message': 'Documento no encontrado'}), 404

@user_bp.route('/api/empleados')
def obtener_empleados():
    usuarios = User.query.all()
    admins = Admin.query.all()
    empleados = [
        {
            'id': u.idUser,
            'name': u.usernameUser,
            'tipo': 'user'
        }
        for u in usuarios
    ] + [
        {
            'id': a.idAdmin,
            'name': a.usernameAdmin,
            'tipo': 'admin'
        }
        for a in admins
    ]
    return jsonify(empleados)

from flask import send_file, jsonify


@user_bp.route('/api/empleado/<string:tipo>/<int:empleado_id>/asistencia')
def obtener_asistencia(tipo, empleado_id):
    mes = request.args.get("mes")  # opcional, formato YYYY-MM
    query = Ingreso.query

    if tipo == 'user':
        usuario = User.query.get(empleado_id)
        if not usuario:
            return jsonify({'success': False, 'message': 'Empleado no encontrado'}), 404
        query = query.filter_by(user_id=empleado_id)
        nombre = usuario.usernameUser

    elif tipo == 'admin':
        admin = Admin.query.get(empleado_id)
        if not admin:
            return jsonify({'success': False, 'message': 'Empleado no encontrado'}), 404
        query = query.filter_by(admin_id=empleado_id)
        nombre = admin.usernameAdmin
    else:
        return jsonify({'success': False, 'message': 'Tipo inválido'}), 400

    # 🔹 Filtrar por mes si viene el parámetro
    if mes:
        try:
            year, month = map(int, mes.split("-"))
            query = query.filter(db.extract("year", Ingreso.fecha) == year,
                                 db.extract("month", Ingreso.fecha) == month)
        except Exception:
            return jsonify({'success': False, 'message': 'Formato de mes inválido'}), 400

    ingresos = query.all()
    eventos = []

    for ingreso in ingresos:
        # Ingreso presente o retardo
        if ingreso.estado in ['Presente', 'Retardo']:
            eventos.append({
                'title': f'Ingreso: {ingreso.hora.strftime("%H:%M")}',
                'start': f"{ingreso.fecha.strftime('%Y-%m-%d')}T{ingreso.hora.strftime('%H:%M:%S')}",
                'className': 'ingreso',
                'tipo': 'ingreso',
                'extendedProps': {
                    'fecha': ingreso.fecha.strftime("%Y-%m-%d"),
                    'hora': ingreso.hora.strftime("%H:%M"),
                    'estado': ingreso.estado,
                    'motivo': ingreso.motivo,
                    'horario': ingreso.horario
                }
            })

        # Ausente
        if ingreso.estado == 'Ausente':
            eventos.append({
                'title': 'Ausente',
                'start': ingreso.fecha.strftime('%Y-%m-%d'),
                'className': 'ausente',
                'tipo': 'ausencia',
                'extendedProps': {
                    'fecha': ingreso.fecha.strftime("%Y-%m-%d"),
                    'estado': ingreso.estado,
                    'motivo': ingreso.motivo,
                    'horario': ingreso.horario
                }
            })

        # Salidas
        if ingreso.salidas:
            for salida in ingreso.salidas:
                eventos.append({
                    'title': f'Salida: {salida.hora_salida.strftime("%H:%M")}',
                    'start': f"{salida.fecha.strftime('%Y-%m-%d')}T{salida.hora_salida.strftime('%H:%M:%S')}",
                    'className': 'salida',
                    'tipo': 'salida',
                    'extendedProps': {
                        'fecha': salida.fecha.strftime("%Y-%m-%d"),
                        'hora': salida.hora_salida.strftime("%H:%M"),
                        'horario': salida.horario
                    }
                })

    return jsonify({'success': True, 'eventos': eventos, 'nombre': nombre, 'tipo': tipo})
