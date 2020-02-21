from web_app.models import User, Tweet, db, Friends
from flask import Blueprint, jsonify, request, render_template, current_app
import tweepy
from dotenv import load_dotenv
import os
import basilica
from sqlalchemy.exc import IntegrityError
from tweepy import TweepError
from sklearn.linear_model import LogisticRegression
import numpy as np

load_dotenv()

TWITTER_API_KEY = os.getenv('TWITTER_API_KEY')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN')
TWITTER_ACCESS_TOKEN_SECRET = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
client = tweepy.API(auth)

routes = Blueprint("routes", __name__)

basilica_api = os.getenv("basilica_api_key")
c = basilica.Connection(basilica_api)

@routes.route("/interactive_tweets", methods=["POST"])
def interactive_tweets():
    username = request.form['name']
    friends = client.friends(username)
    highest_count = 0
    most_interacted_list = []
    for friend in friends:
        tweets = client.user_timeline(friend.screen_name, tweet_mode='extended')
        for tweet in tweets:
            interactions = tweet.retweet_count + tweet.favorite_count
            if interactions >= highest_count:
                most_interacted = str(tweet.user.screen_name) + ':' + str(tweet.full_text)
                highest_count = interactions
        most_interacted_list.append(most_interacted)
        highest_count = 0
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
                interactions = tweet.retweet_count + tweet.favorite_count
                db.session.add(Tweet(user_id=user_obj.id, status=tweet.full_text, id=tweet.id, interactions=interactions))
            db.session.commit()
            for friend in friends:
                db.session.add(Friends(user_id=friend, friend_of_id=user_obj.id))
            db.session.commit()
        except TweepError:
            return render_template('error_new_user.html')

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


@routes.route("/add_user_interactive", methods=['POST'])
def add_to_database():
    user=request.form['name']
    tweets = client.user_timeline(user, tweet_mode="extended", count=200, exclude_replies=True, include_rts=False)
    userid = client.get_user(user).id
    try:
        db.session.add(User(name=user, id=userid))
        db.session.commit()
        for tweet in tweets:
            interactions = tweet.retweet_count + tweet.favorite_count
            embedded = c.embed_sentence(tweet.full_text)
            db.session.add(Tweet(user_id=userid, status=tweet.full_text, id=tweet.id, embedding=embedded, interactions=interactions))
        db.session.commit()
    except IntegrityError:
        pass
    return jsonify({"message": "User and existing tweets added to database"})

@routes.route("/model_interactions")
def train_model():
    user = request.form("name")
    userid = client.get_user(user).id
    new_tweet = request.form['new_tweet']
    new_tweet_embedded = c.embed_sentence(new_tweet, model='twitter')
    model_tweets = Tweet.query.filter(Tweet.user_id == userid).all()
    embeddings_array = np.array([tweet.embedding for tweet in model_tweets])
    interactions_array = np.array([tweet.interactions for tweet in model_tweets])
    classifier = LogisticRegression().fit(embeddings_array, interactions_array)
    results = classifier.predict(new_tweet_embedded)
    return render_template('likely_interactive.html', prediction_results=results, tweet=new_tweet, user=user)
