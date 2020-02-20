from web_app.models import User, Tweet, db, Friends
from flask import Blueprint, jsonify, request, render_template, current_app
import tweepy
from dotenv import load_dotenv
import os
import basilica
from sqlalchemy.exc import IntegrityError
from tweepy import TweepError

routes = Blueprint("routes", __name__)

load_dotenv()

basilica_api = os.getenv("basilica_api_key")
c = basilica.Connection(basilica_api)

@routes.route("/interactive_tweets", methods=["POST"])
def interactive_tweets():
    client = current_app.config['TWITTER_API_CLIENT']
    username = request.form['name']
    friends = client.friends_id(username)
    highest_count = 0
    most_interacted_list = []
    for friend in friends:
        tweets = client.user_timeline(user_id=friend, tweet_mode='extended')
        for tweet in tweets:
            interactions = tweet.retweet_count + tweet.favorite_count
            if interactions >= highest_count:
                most_interacted = str(tweet.user.screen_name) + ':' + str(tweet.full_text)
                highest_count = interactions
        most_interacted_list.append(most_interacted)
        highest_count = 0
    #  could create model to predict whether a tweet is going to be interactive among your followers
    return jsonify(most_interacted_list)


@routes.route("/")
def index():
    return render_template("homepage.html")


@routes.route("/users")
@routes.route("/users.json")
def users():
    users = User.query.all()  # returns a list of <class 'alchemy.User'>

    users_response = []
    for u in users:
        user_dict = u.__dict__
        del user_dict["_sa_instance_state"]
        users_response.append(user_dict)
    return jsonify(users_response)


@routes.route("/users/create", methods=["POST"])
def create_user():
    client = current_app.config["TWITTER_API_CLIENT"]
    db.session.commit()
    print("CREATING A NEW USER...")
    print("FORM DATA:", dict(request.form))
    name = request.form["name"]
    if len(name) > 0:
        try:
            user_obj = client.get_user(name)
            db.session.add(User(name=name, id=user_obj.id))
            db.session.commit()
            tweets = client.user_timeline(name, tweet_mode="extended")
            friends = client.friends_ids(name)
            for tweet in tweets:
                embedding = c.embed_sentence(tweet, model='twitter')
                db.session.add(Tweet(user_id=user_obj.id, status=tweet.full_text, id=tweet.id, embedding=embedding))
            db.session.commit()
            for friend in friends:
                db.session.add(Friends(user_id=friend, friend_of_id=user_obj.id))
            db.session.commit()
        except TweepError:
            return render_template('error_new_user.html')
        except IntegrityError:
            return render_template('user_exists.html')

        print(jsonify({"message": "CREATED OK", "name": name}))
        return render_template('new_user_created.html')
    else:
        print(jsonify({"message": "OOPS PLEASE SPECIFY A NAME!"}))
        return render_template('error_new_user.html')


@routes.route("/tweets")
def tweets():
    tweets = db.session.query(Tweet.user_id, Tweet.status).all()
    tweets_list = []
    for tweet in tweets:
        tweet_dict = {'user_id': tweet[0], 'tweet': tweet[1]}
        tweets_list.append(tweet_dict)
    return jsonify(tweets_list)


@routes.route("/friends")
def friends():
    friends = Friends.query.all()
    friends_list = []
    for friend in friends:
        friends_dict = friend.__dict__
        del friends_dict['_sa_instance_state']
        friends_list.append(friends_dict)
    return jsonify(friends_list)


@routes.route("/similarities")
def similarities():
    return render_template('similarities.html')