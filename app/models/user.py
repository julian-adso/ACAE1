
import hashlib
from app.utilidad.extensions import db

class User(db.Model):
    
    idUser = db.Column(db.Integer, autoincrement=True, primary_key=True)
    login_id = db.Column(db.Integer, db.ForeignKey('login.idLogin'), nullable=False)
    usernameUser = db.Column(db.String(50), unique=True, nullable=False)
    passwordUser = db.Column(db.String(100), nullable=False)
    documentUser = db.Column(db.String(100), nullable=False)
    phoneUser = db.Column(db.String(15), nullable=False)
    emailUser = db.Column(db.String(100), nullable=False)
    horario = db.Column(db.Enum('Mañana', 'Tarde', 'Noche'), nullable=False)
    
    login = db.relationship('Login', back_populates ='users')
    salidas = db.relationship('Salida', backref = 'user')
    
    def set_password(self, password: str):
        self.passwordUser = hashlib.sha1(password.encode('utf-8')).hexdigest()

    def check_password(self, password: str) -> bool:
        return self.passwordUser == hashlib.sha1(password.encode('utf-8')).hexdigest()
