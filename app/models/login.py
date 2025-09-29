import hashlib
from app import db

class Login(db.Model):
    __tablename__ = 'login'
    
    idLogin = db.Column(db.Integer, autoincrement=True, primary_key=True)
    usernameLogin = db.Column(db.String(50), unique=True, nullable=False)
    passwordLogin = db.Column(db.String(100), nullable=False)
    
    admins = db.relationship('Admin', back_populates='login')
    users = db.relationship('User', back_populates='login')
    super = db.relationship('Super', back_populates='login')
    
    def set_password(self, password: str):
        """"Genera el SHA1 y lo guarda en passwordLogin"""
        self.passwordLogin = hashlib.sha1(password.encode('utf-8')).hexdigest()
        
    def check_password(self, password: str) -> bool:
        """Verifica si el SHA1 de password coincide con passwordLogin"""
        return self.passwordLogin == hashlib.sha1(password.encode('utf-8')).hexdigest()