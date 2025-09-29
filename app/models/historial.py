
from app import db

class HistorialCambio(db.Model):
    
    idCambio = db.Column(db.Integer, autoincrement=True, primary_key=True)
    ingreso_id = db.Column(db.Integer, db.ForeignKey('ingreso.idIngreso'), nullable=False)
    fecha_cambio = db.Column(db.DateTime, nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    usuario = db.Column(db.String(50), nullable=False)  # Quién realizó el cambio

    ingreso = db.relationship('Ingreso', backref='historial_cambios')
    