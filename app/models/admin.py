import hashlib
from app.utilidad.extensions import db

class Admin(db.Model):
    __tablename__= "admin"
    
    idAdmin = db.Column(db.Integer, autoincrement=True, primary_key=True)
    login_id = db.Column(db.Integer, db.ForeignKey('login.idLogin'), nullable=False)
    usernameAdmin = db.Column(db.String(50), unique=True, nullable=False)
    passwordAdmin = db.Column(db.String(100), nullable=False)
    documentAdmin = db.Column(db.String(100), nullable=False)
    phoneAdmin = db.Column(db.String(15), nullable=False)
    emailAdmin = db.Column(db.String(100), nullable=False)
    horario = db.Column(db.Enum('Mañana', 'Tarde', 'Noche'), nullable=False)
    
    login = db.relationship('Login', back_populates='admins')
   
    def set_password(self, password: str):
        self.passwordAdmin = hashlib.sha1(password.encode('utf-8')).hexdigest()

    def check_password(self, password: str) -> bool:
        return self.passwordAdmin == hashlib.sha1(password.encode('utf-8')).hexdigest()
