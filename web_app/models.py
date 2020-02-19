from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()

migrate = Migrate()



class User(db.Model):
    id = db.Column(db.BIGINT, primary_key=True)
    name = db.Column(db.String(128))


class Tweet(db.Model):
    id = db.Column(db.BIGINT, primary_key=True)
    status = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    embedding = db.Column(db.PickleType)

class Friends(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    screenname = db.Column(db.String)
    friend_of_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)