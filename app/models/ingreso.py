from app.utilidad.extensions import db

class Ingreso(db.Model):
    __tablename__ = "ingreso"
    
    idIngreso = db.Column(db.Integer, autoincrement=True, primary_key=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.idUser'), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.idAdmin'), nullable=True)
    
    rol=db.Column(db.Enum('User','Admin'), nullable=False) # Rol del usuario    
    
    fecha = db.Column(db.Date, nullable=False)         # Día
    hora = db.Column(db.Time, nullable=True)          # Hora exacta
    horario = db.Column(db.Enum('Mañana', 'Tarde', 'Noche'), nullable=True) # Ejemplo: "Mañana", "Tarde", "Noche"
    estado = db.Column(db.Enum('Presente', 'Retardo', 'Ausente'), nullable=False) # Estado del ingreso
    motivo = db.Column(db.String(255)) # Motivo del ingreso, si aplica

    user = db.relationship('User', backref='ingresos', lazy=True) 
    admin = db.relationship('Admin', backref='ingresos', lazy=True)
    salidas = db.relationship('Salida', back_populates='ingreso', lazy=True)