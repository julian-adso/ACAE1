
from app import db

class Salida(db.Model):
    __tablename__ = 'salida'
    
    idSalida = db.Column(db.Integer, autoincrement=True, primary_key=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.idUser'), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.idAdmin'), nullable=True)
    
    rol=db.Column(db.Enum('User', 'Admin'), nullable=False)
    
    ingreso_id = db.Column(db.Integer, db.ForeignKey('ingreso.idIngreso'), nullable=False)
    super_id = db.Column(db.Integer, db.ForeignKey('super.idSuper'), nullable=True)

    fecha = db.Column(db.Date, nullable=False)
    hora_salida = db.Column(db.Time, nullable=False)
    horario = db.Column(db.Enum('Mañana', 'Tarde', 'Noche'), nullable=False)
    
    ingreso = db.relationship('Ingreso', back_populates='salidas')