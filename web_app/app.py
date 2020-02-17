from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import tweepy
from dotenv import load_dotenv
import os
import basilica
import sqlite3

from sqlalchemy.sql.functions import user
from tweepy import TweepError

load_dotenv()

basilica_api = os.getenv("basilica_api_key")
c = basilica.Connection(basilica_api)

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", default="OOPS")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", default="OOPS")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", default="OOPS")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", default="OOPS")

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


auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
client = tweepy.API(auth)

elon_tweets = client.user_timeline("elonmusk", tweet_mode="extended")
for tweet in elon_tweets:
    print(tweet.full_text)
one_tweet = client.user_timeline('elonmusk', tweet_mode='extended', count=1)
print(one_tweet[0].full_text)


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
    conn = sqlite3.connect('web_app_cai_nowicki.db')
    c = conn.cursor()
    print("CREATING A NEW USER...")
    print("FORM DATA:", dict(request.form))
    name = request.form["name"]
    if len(name) > 0:
        print(name)
        db.session.add(User(name=name))
        try:
            client.get_user(name)
            tweets = client.user_timeline(name, tweet_mode="extended")
            query = "SELECT id FROM user WHERE name = %s" % name
            #the dynamic string here doesn't work, try something else
            user_id = c.execute(query).fetchone()
            print(user_id)
            db.session.add(Tweet(user_id=user_id, status=tweets[0].full_text))
        except TweepError:
            return render_template('error_new_user.html')
        db.session.commit()
        print(jsonify({"message": "CREATED OK", "name": name}))
        return render_template('new_user_created.html')
    else:
        print(jsonify({"message": "OOPS PLEASE SPECIFY A NAME!"}))
        return render_template('error_new_user.html')

users = User.query.all()  # returns a list of <class 'alchemy.User'>

users_response = []
for u in users:
    user_dict = u.__dict__
    del user_dict["_sa_instance_state"]
    users_response.append(user_dict)