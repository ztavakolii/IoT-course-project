from models import Session
from app import db

Session.query.delete()
db.session.commit()
