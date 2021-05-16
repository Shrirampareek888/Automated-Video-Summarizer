import json
import helpers.TextSummarization as ts
import helpers.YoutubeHelper as yt
from pymongo import MongoClient
from flask import Flask, render_template, url_for, request, flash, redirect, jsonify, send_file
from flask_cors import CORS, cross_origin
from flask_bcrypt import Bcrypt
#import speech_recognition as sr
import os
import sys
sys.path.insert(0, os.getcwd()+"/helpers")
#from werkzeug.utils import secure_filename

app = Flask(__name__)
bcrypt = Bcrypt(app)
client = MongoClient('localhost', 27017)
db = client.cnt_db
users = db.users

ALLOWED_EXTENSIONS = {'mp3', 'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
cors = CORS(app, resources={r"/foo": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/')
def index():
    return render_template('login.html')


@app.route('/downloadfile/<text>', methods=['GET', 'POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def testfn(text):
    print("INSIDE FLASK")
    ext_summary = ts.extractive_summary(text)
    print("EXTRACTIVE DONE")
    abs_summary = ts.abstractive_summary(text)
    print("ABSTRACTIVE DONE")
    ts.generate_pdf(ext_summary, abs_summary)
    f = open("./static/notes.pdf", 'rb')
    return send_file(f, attachment_filename='minutes_of_meeting.pdf')


@app.route('/youtube/', methods=['GET', 'POST'])
@cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
def get_youtube_transcripts():
    url = request.data.decode('utf-8')
    text = yt.get_transcripts(url)
    return text


@app.route("/login", methods=['GET', 'POST'])
def employee_login():
    print(request.form['email'])
    print(request.form['password'])
    user_cred = users.find_one({'email': request.form['email']}, {
        'email': 1, 'password': 1})
    if(not bool(user_cred)):
        return render_template('signup.html')
    if(bcrypt.check_password_hash(user_cred['password'], request.form['password'])):
        return render_template('index.html')
    else:
        return render_template('login.html')


if __name__ == "__main__":
    print('started')
    app.run(debug=True)
