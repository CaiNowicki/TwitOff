from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///web_app_cai_nowicki.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))


class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))


@app.route("/")
def index():
    return render_template("homepage.html")

@app.route("/users")
@app.route("/users.json")
def users():
    users = User.query.all()  # returns a list of <class 'alchemy.User'>

    users_response = []
    for u in users:
        user_dict = u.__dict__
        del user_dict["_sa_instance_state"]
        users_response.append(user_dict)

    return jsonify(users_response)


@app.route("/users/create", methods=["POST"])
def create_user():
    print("CREATING A NEW USER...")
    print("FORM DATA:", dict(request.form))
    name = request.form["name"]
    if len(name) > 0:
        print(name)
        db.session.add(User(name=name))
        db.session.commit()
        print(jsonify({"message": "CREATED OK", "name": name}))
        return render_template('new_user_created.html')
    else:
        print(jsonify({"message": "OOPS PLEASE SPECIFY A NAME!"}))
        return render_template('error_new_user.html')

