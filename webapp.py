
from profanityfilter import ProfanityFilter
import pymongo
import sys


from flask import Flask, redirect, url_for, session, request, jsonify, Markup
from flask_oauthlib.client import OAuth
#from flask_oauthlib.contrib.apps import github #import to make requests to GitHub's OAuth
from flask import render_template

import pprint
import os

# This code originally from https://github.com/lepture/flask-oauthlib/blob/master/example/github.py
# Edited by P. Conrad for SPIS 2016 to add getting Client Id and Secret from
# environment variables, so that this will work on Heroku.
# Edited by S. Adams for Designing Software for the Web to add comments and remove flash messaging

app = Flask(__name__)

app.debug = False #Change this to False for production
#os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' #Remove once done debugging
app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)
oauth.init_app(app) #initialize the app to be able to make requests for user information

#Set up GitHub as OAuth provider
github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'], #your web app's "username" for github's OAuth
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],#your web app's "password" for github's OAuth
    request_token_params={'scope': 'user:email'}, #request read-only access to the user's email.  For a list of possible scopes, see developer.github.com/apps/building-oauth-apps/scopes-for-oauth-apps
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',  
    authorize_url='https://github.com/login/oauth/authorize' #URL for github's OAuth login
)
connection_string = os.environ["MONGO_CONNECTION_STRING"]
db_name = os.environ["MONGO_DBNAME"]
    
client = pymongo.MongoClient(connection_string)
db = client[db_name]
collection = db['Form-Project'] #1. put the name of your collection in the quotes
pf = ProfanityFilter()

#collection.insert_one({ 'test': 'test1'})
#context processors run before templates are rendered and add variable(s) to the template's context
#context processors must return a dictionary 
#this context processor adds the variable logged_in to the conext for all templates
@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

@app.route('/')
def home():
    return render_template('home.html')

#redirect to GitHub's OAuth page and confirm callback URL
@app.route('/login')
def login():   
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='https')) #callback URL must match the pre-configured callback URL

@app.route('/logout')
def logout():
    session.clear()
    return render_template('message.html', message='You were logged out')

@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        message = 'Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args)      
    else:
        try:
            print(resp)
            session['github_token'] = (resp['access_token'], '') #save the token to prove that the user logged in
            session['user_data']=github.get('user').data
            #pprint.pprint(vars(github['/email']))
            #pprint.pprint(vars(github['api/2/accounts/profile/']))
            message='You were successfully logged in as ' + session['user_data']['login'] + '.'
        except Exception as inst:
            session.clear()
            print(inst)
            message='Unable to login, please try again.  '
    return render_template('message.html', message=message)


@app.route('/discussion')
def renderdiscussion():
    return render_template('discussion.html', post1 = get_formatted_posts("Favorite Shounen Anime"), post2 = get_formatted_posts("Topic Title"), post3 = get_formatted_posts("Collapsible Group 3"))

@app.route('/rules')
def renderrules():
    return render_template('rules.html')

@app.route('/googleb4c3aeedcc2dd103.html')
def render_google_verification():
    return render_template('googleb4c3aeedcc2dd103.html')

#the tokengetter is automatically called to check who is logged in.
@github.tokengetter
def get_github_oauth_token():
    return session['github_token']

@app.route('/discussionfs',methods=['GET','POST'])
def renderdiscussionfs():
    if 'message1' in request.form:
        fShounen={'username': session['user_data']['login'],
        'post': pf.censor(request.form['message1']),
        'topic': "Favorite Shounen Anime" }
    elif 'message2' in request.form:
        fShounen={'username': session['user_data']['login'],
        'post': pf.censor(request.form['message2']),
        'topic': "Topic Title" }
    elif 'message3' in request.form:
        fShounen={'username': session['user_data']['login'],
        'post': pf.censor(request.form['message3']),
        'topic': "Collapsible Group 3" }


    collection.insert_one(fShounen)
    return render_template('discussion.html', post1 = get_formatted_posts("Favorite Shounen Anime"), post2 = get_formatted_posts("Topic Title"), post3 = get_formatted_posts("Collapsible Group 3"))

def get_formatted_posts(topic):
    posts = collection.find({"topic": topic})


    formatted_posts = ""
    for post in posts:
    
        formatted_posts = formatted_posts  + Markup('<div class="BD"><p>'+ post["username"] + "</p><p>"+  post["post"]+'</p><form <input type="submit" value="Submit"><button name="Up" value="'+str( post ["_id"])+'"><i onclick="myFunction(this)" class="fa fa-thumbs-up"></i><i onclick="myFunction(this)" class="fa fa-thumbs-down"></i></form></button></div>')
    return formatted_posts

if __name__ == '__main__':
    app.run(debug=True)
