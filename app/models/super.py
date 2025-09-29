import hashlib
from app import db

class Super(db.Model):
    idSuper = db.Column(db.Integer, autoincrement=True, primary_key=True)
    login_id = db.Column(db.Integer, db.ForeignKey('login.idLogin'), nullable=False)
    usernameSuper = db.Column(db.String(50), unique=True, nullable=False)
    passwordSuper = db.Column(db.String(100), nullable=False)
    documentSuper = db.Column(db.String(100), nullable=False)
    phoneSuper = db.Column(db.String(15), nullable=False)
    emailSuper = db.Column(db.String(100), nullable=False)
    horario = db.Column(db.Enum('Mañana', 'Tarde', 'Noche'), nullable=False)

    login = db.relationship('Login', back_populates='super')

    def set_password(self, password: str):
        self.passwordSuper = hashlib.sha1(password.encode('utf-8')).hexdigest()

    def check_password(self, password: str) -> bool:
        return self.passwordSuper == hashlib.sha1(password.encode('utf-8')).hexdigest()