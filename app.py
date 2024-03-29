import json
import gridfs
import base64
import helpers.TextSummarization as ts
import helpers.YoutubeHelper as yt
from pymongo import MongoClient
from flask import Flask, render_template, url_for, request, flash, redirect, jsonify, send_file, session
from flask_cors import CORS, cross_origin
from flask_bcrypt import Bcrypt
import os
import sys
sys.path.insert(0, os.getcwd()+"/helpers")
# from werkzeug.utils import secure_filename

app = Flask(__name__)
bcrypt = Bcrypt(app)
client = MongoClient('localhost', 27017)
db = client.cnt_db
users = db.users
fs = gridfs.GridFS(db)

ALLOWED_EXTENSIONS = {'mp3', 'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
cors = CORS(app, resources={r"/foo": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SECRET_KEY'] = '14ec258c169f5c19f78385bcc83a51df7444624b2ff90449b4a9832e6fe706a1'


@app.route('/')
def index():
    userscnt = db.users.count()
    pdfcnt = db.pdfs.count()
    return render_template('index.html', cnt = userscnt, pdf = pdfcnt)


@app.route('/login-page')
def show_login_page():
    return render_template('login-signup.html')



@app.route('/dashboard')
def show_dashboard():
    return render_template('dashboard.html')
# @app.route('/downloadfile/<file_name>', methods=['GET', 'POST'])
# @cross_origin(origin='*', headers=['Content-Type', 'Authorization'])
# def download(file_name):

#     return send_file(f, attachment_filename=file_name)


@app.route("/login", methods=['GET', 'POST'])
def login():
    print(request.form['email'])
    print(request.form['password'])
    user_cred = users.find_one({'email': request.form['email']}, {
        'name': 1, 'email': 1, 'password': 1})
    if(not bool(user_cred)):
        return render_template('login-signup.html', message="User not found. Please Sign Up!", classm="alert alert-danger")
    if(bcrypt.check_password_hash(user_cred['password'], request.form['password'])):
        # create session variable with email
        session['email'] = user_cred['email']
        return render_template('dashboard.html', name=user_cred['name'])
    else:
        return render_template('login-signup.html', message="Incorrect password!", classm="alert alert-danger")


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if(request.form['pwd'] != request.form['rpwd']):
        return render_template('login-signup.html', message="Passwords don't match!", classm="alert alert-danger")

    name = request.form['fname'] + " " + request.form['lname']
    password_hash = bcrypt.generate_password_hash(request.form['pwd'], 10)
    user_details = {"name": name,
                    "email": request.form['email'],
                    "password": password_hash}
    empr_id = db.users.insert_one(user_details).inserted_id
    print(empr_id)
    
    return render_template('login-signup.html', message="Sign up successful", classm="alert alert-success")


@app.route("/generate-notes", methods=['GET', 'POST'])
def generate_notes():
    # if 'email' not in session:
    #     return render_template('login.html')
    url = request.form['url']
    filename = request.form['name']
    print(filename)
    text = yt.get_transcripts(url)
    ext_summary = ts.extractive_summary(text)
    print("EXTRACTIVE DONE")
    abs_summary = ts.abstractive_summary(text)
    print("ABSTRACTIVE DONE")
    ts.generate_pdf(ext_summary, abs_summary)
    file_data = {"name": filename+'.pdf', "extsum": ext_summary, "absum": abs_summary}
    db.pdfs.insert_one(file_data)
    f = open("./static/notes.pdf", 'rb')
    return send_file(f, attachment_filename=filename+".pdf")


@app.route("/edit-profile", methods=['GET', 'POST'])
def edit():
    if 'email' not in session:
        return render_template('login.html')
    updated_cred = users.update_one({'email': request.form['email']}, {
        'name': request.form['name'], 'password': request.form['password'], 'number': request.form['cnum']})
    print(updated_cred)


@app.route("/my-pdfs", methods=['GET', 'POST'])
def mypdfs():
    pdfs = []
    for file in db.pdfs.find():
        print(file['name'])
        pdfs.append(file['name'])
    return render_template("mypdfs.html", pdfs=pdfs)


@app.route("/download/<file_name>", methods=['GET', 'POST'])
def download(file_name):
    file = db.pdfs.find_one({"name": file_name})
    ext_summary = file['extsum']
    abs_summary = file['absum']
    ts.generate_pdf(ext_summary, abs_summary)
    print(ext_summary)
    f = open("./static/notes.pdf", 'rb')
    return send_file(f, attachment_filename=file_name+".pdf")


if __name__ == "__main__":
    print('started')
    app.run(debug=True, use_reloader=False)
