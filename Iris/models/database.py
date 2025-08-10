from flask_sqlalchemy import SQLAlchemy
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# Association table for ApiToken and ApiScript (many-to-many)
token_api_association = db.Table('token_api_association',
    db.Column('token_id', db.Integer, db.ForeignKey('api_token.id'), primary_key=True),
    db.Column('script_id', db.String(100), db.ForeignKey('api_script.id'), primary_key=True)
)

# Association table for User and ApiScript (for token generation permissions)
user_api_permission = db.Table('user_api_permission',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('script_id', db.String(100), db.ForeignKey('api_script.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(80), nullable=False, default='user') # 'admin' or 'user'
    email = db.Column(db.String(120), unique=True, nullable=True)
    api_all_access = db.Column(db.Boolean, default=False, nullable=False) # Nouveau champ
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationship for user's API permissions
    api_permissions = db.relationship('ApiScript', secondary=user_api_permission, lazy='subquery',
                                      backref=db.backref('users_with_permission', lazy=True))
    # Relationship for tokens created by this user
    created_tokens = db.relationship('ApiToken', backref='creator', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class ApiScript(db.Model):
    id = db.Column(db.String(100), primary_key=True)
    description = db.Column(db.Text, nullable=True) # New field
    doc = db.Column(db.Text, nullable=True) # New field
    is_public = db.Column(db.Boolean, default=True, nullable=False)
    is_online = db.Column(db.Boolean, default=False, nullable=False) # Changé à False

    # Relationship for tokens that can access this script
    tokens_with_access = db.relationship('ApiToken', secondary=token_api_association, lazy='subquery',
                                         backref=db.backref('accessible_scripts', lazy=True))

class ApiToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    token = db.Column(db.String(128), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    token_type = db.Column(db.String(20), nullable=False, default='app') # 'universal' or 'app'
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Link to the user who created it

class LogSystem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    level = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    details = db.Column(db.JSON, nullable=True)

    def __repr__(self):
        return f'<LogSystem {self.id} - {self.level}>'

class LogWeb(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    ip_address = db.Column(db.String(45))
    request = db.Column(db.Text)
    status = db.Column(db.String(20))
    message = db.Column(db.Text)

    user = db.relationship('User')

    def __repr__(self):
        return f'<LogWeb {self.id} - {self.status}>'

class LogApi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    token = db.Column(db.String(45), nullable=True)
    ip_address = db.Column(db.String(45))
    request = db.Column(db.Text)
    name = db.Column(db.Text)
    status = db.Column(db.String(20))
    response = db.Column(db.Text)
    message = db.Column(db.Text)

    def __repr__(self):
        return f'<LogApi {self.id} - {self.status}>'

class LogSocket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ip_address = db.Column(db.String(45))
    method = db.Column(db.String(10)) # GET, POST, PUT, DELETE, etc.
    path = db.Column(db.Text) # Full URI path
    status_code = db.Column(db.Integer) # HTTP status code
    response_time_ms = db.Column(db.Integer, nullable=True) # Response time in milliseconds
    request_body = db.Column(db.Text, nullable=True) # Optional: store request body for debugging

    def __repr__(self):
        return f'<LogSocket {self.id} - {self.method} {self.path} - {self.status_code}>'

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
