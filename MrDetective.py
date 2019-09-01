import json
import urllib.request
from flask import Flask, render_template, session, request, flash, redirect, url_for, abort, jsonify
from passlib.hash import sha256_crypt
from functools import wraps
import random
import string
from datetime import datetime
import time
from helper import Database, LOG
from requests_toolbelt import MultipartEncoder
import requests
import os
import boto3

app = Flask(__name__)
app.secret_key = os.getenv('APP_SECRET').strip()

s3_client = boto3.session.Session().client('s3',
                                           region_name=os.getenv('S3_REGION').strip(),
                                           endpoint_url=os.getenv('S3_ENDPOINT').strip(),
                                           aws_access_key_id=os.getenv('S3_ACCESS_KEY').strip(),
                                           aws_secret_access_key=os.getenv('S3_SECRET_KEY').strip())


# session['permission'] = ban, train, unban, getss, delss, add_admin, remove_admin
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(request.referrer)

    return wrap


def permission_getss(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'getss' in session['permission']:
            return f(*args, **kwargs)
        else:
            flash("You don't have Permission to perform that")
            return redirect(request.referrer)

    return wrap


def permission_delss(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'delss' in session['permission']:
            return f(*args, **kwargs)
        else:
            flash("You don't have Permission to perform that")
            return redirect(request.referrer)

    return wrap


def permission_ban(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'ban' in session['permission']:
            return f(*args, **kwargs)
        else:
            flash("You don't have Permission to perform that")
            return redirect(request.referrer)

    return wrap


def permission_train(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'train' in session['permission']:
            return f(*args, **kwargs)
        else:
            flash("You don't have Permission to perform that")
            return redirect(request.referrer)

    return wrap


def permission_manage(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'manage' in session['permission']:
            return f(*args, **kwargs)
        else:
            flash("You don't have Permission to perform that")
            return redirect(request.referrer)

    return wrap


def escape(text):
    return str(text.replace(";", '').replace("{", '').replace("}", '').replace("'", '').replace('"', '&quot;'))


@app.route('/auth/', methods=["GET", "POST"])
def auth():
    try:
        db = Database()
        if request.method == "POST" and request.form['secretkey'] == db.read('SELECT secretkey from server_info')[0][0]:
            b3id = int(request.form['b3id'])
            guid = request.form['guid']
            level = int(request.form['level'])
            if level >= 100:
                power = 'ban, train, getss, delss, manage'
            elif level >= 16:
                power = 'ban, train, getss'
            else:
                power = 'getss'
            authkey = request.form['authkey']
            db.write(
                '''UPDATE users SET B3ID = (%s), GUID = (%s) ,Permissions = (%s), authkey = (%s) WHERE authkey = (%s)''',
                b3id, guid, power, None, authkey)
            db.close()
        return 'ok'
    except Exception as e:
        LOG.exception(e)
        return 'error'


@app.route('/', methods=["POST", 'GET'])
def home():
    try:
        if 'authkey' in session and session['authkey'] is not None:
            flash("Welcome ! It's look like you are new to here when you visit the Black Assassins Server type"
                  " !webauth {} to complete the registration".format(session['authkey']))
        db = Database()
        session['last_ss'] = int(db.read('SELECT ID FROM screenshots ORDER BY ID DESC LIMIT 1')[0][0])
        ss = db.read('SELECT * FROM screenshots WHERE ID <= (%s) ORDER BY ID DESC LIMIT 27', session['last_ss'])
        ss_new = []
        db.close()
        for s in ss:
            s = list(s)
            s[-1] = datetime.fromtimestamp(s[-1])
            s[1] = escape(s[1])
            s[4] = escape(str(s[4])[:90].strip(',').strip(' '))
            ss_new.append(s)
        ss = ss_new
        if request.method == "POST":
            print(request.form)
            return render_template('home.html', ss=ss)
        else:
            return render_template('home.html', ss=ss)
    except Exception as e:
        LOG.exception(e)
        return render_template('home.html', ss=[])


@app.route('/load/')
def load():
    db = Database()
    session['last_ss'] -= 27
    if session['last_ss'] <= 0:
        session['last_ss'] = int(db.read('SELECT ID FROM screenshots ORDER BY ID DESC LIMIT 1')[0][0])
    ss = db.read('SELECT * FROM screenshots WHERE ID <= (%s) ORDER BY ID DESC LIMIT 27', session['last_ss'])
    db.close()
    ss_new = []
    for s in ss:
        s = list(s)
        s[-1] = datetime.fromtimestamp(s[-1])
        s[1] = escape(s[1])
        s[4] = escape(str(s[4])[:90].strip(',').strip(' '))
        ss_new.append(s)
    ss = ss_new
    return render_template('card_generator.html', ss=ss)


@app.route('/ss/')
def reroute():
    return redirect(url_for('imageview', ssid=1))


@app.route('/ss/<ssid>/')
def imageview(ssid):
    db = Database()
    ss = db.read('SELECT * FROM screenshots WHERE ID = (%s) ORDER BY ID DESC LIMIT 1', ssid)
    db.close()
    try:
        return render_template("imageview.html", data=ss)
    except Exception as e:
        LOG.exception(e)
        flash('ScreenShot Not Found')
        return redirect(url_for('home'))


@app.route('/login/', methods=["POST"])
def login():
    try:
        if request.method == "POST":
            db = Database()
            username = request.form['username'].lower()
            users = db.read('SELECT Username,password,AuthKey,GUID,B3ID,Permissions FROM users WHERE username = (%s)',
                            username)
            if not users:
                users = db.read('''SELECT Username,password,AuthKey,GUID,B3ID,Permissions FROM users WHERE
                                Email = (%s)''', username)
            db.close()
            # users = [['supiri', 'pass', 'auth', '123', '3', [True, True, True, True, True]]]

            if users and sha256_crypt.verify(request.form['password'], users[0][1]):
                # if request.form['username'].lower() == users[0][0] and request.form['password'] == users[0][1]:
                session['logged_in'] = True
                session['username'] = users[0][0].title()
                session['authkey'] = users[0][2]
                session['guid'] = users[0][3]
                session['b3id'] = users[0][4]
                session['permission'] = users[0][5]
                flash('Welcome {}!'.format(users[0][0].title()))
                return redirect(request.referrer)
            else:
                flash('Invalid credentials. Try Again.')
                return redirect(request.referrer)
    except Exception as e:
        LOG.exception(e)
        return redirect(request.referrer)


@app.route('/register/', methods=["POST"])
def register():
    try:
        if request.method == "POST":
            db = Database()
            displayname = request.form['name']
            username = str(request.form['regusername']).lower()
            password = sha256_crypt.encrypt(str(request.form['regpassword']))
            email = request.form['email']
            AuthKey = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            x = db.read("SELECT * FROM users WHERE Username = (%s)", username)
            y = db.read("SELECT * FROM users WHERE Email = (%s)", email)
            if x:
                flash('Username Already in Use')
                return redirect(request.referrer)
            if y:
                flash('Your Email is already Registered')
                return redirect(request.referrer)
            db.write('''INSERT INTO users(Name,Username,Password,Email,AuthKey) VALUES(%s,%s,%s,%s,%s)''', displayname,
                     username, password, email, AuthKey)
            db.close()
            flash('You Have Successfully Registered !')
            return redirect(request.referrer)
    except Exception as e:
        LOG.exception(e)
        return redirect(url_for(home))


@app.route('/logout/')
@login_required
def logout():
    try:
        session.clear()
        flash("You have been logged out!")
        return redirect(request.referrer)
    except Exception as e:
        LOG.exception(e)
        return render_template("home.html")


@app.route('/ban/<ssid>')
@permission_ban
def ban_player(ssid):
    try:
        db = Database()
        id = str(db.read('''SELECT B3ID from ScreenShots where ID = (%s)''', ssid)[0][0])

        m = MultipartEncoder(
            fields={"b3id": str(session['b3id']), "cmd": 'ban', "args": '@' + id,
                    "args2": '^3WallHacker^0|^1Proof- https://mrdetective.supiritech.com/ss/{}'.format(ssid),
                    "secretkey": db.read('SELECT secretkey from server_info')[0][0]}
        )
        ip, port, url = db.read('SELECT b3_ip,b3_port,b3_url from server_info')[0]
        LOG.error('http://{}:{}/{}'.format(ip, port, url))
        r = str(requests.post('http://{}:{}/{}'.format(ip, port, url), data=m,
                              headers={'Content-Type': m.content_type}).text)
        if 'true' in str(r):
            data = db.write('''UPDATE ScreenShots SET banned = (%s) WHERE ID = (%s)''', session['username'], str(ssid))
            flash('Player Was Successfully Banned')
        else:
            flash('There was a error while banning the player, Try Again in Bit !')
            flash('Make Sure You are Connected to Server Before Banning Again')
        db.close()
        return redirect(request.referrer)
    except:
        flash('Something Went Wrong')
        return redirect(request.referrer)


@app.route('/unban/<ssid>')
@permission_ban
def unban_player(ssid):
    try:
        db = Database()
        db.write('''UPDATE screenshots SET Banned = (%s) WHERE ID = (%s)''', None, ssid)
        flash("B3 Didn't Response to your Ban Request")
        flash("You have to Manually unban the Player via b3")
        db.close()
        return redirect(request.referrer)
    except Exception as e:
        LOG.exception(e)
        flash('Something Went Wrong')
        return redirect(request.referrer)


@app.route('/submit_ss/', methods=["POST"])
def submit_ss():
    try:
        db = Database()
        if request.method == "POST" and request.form['secretkey'] == db.read('SELECT secretkey from server_info')[0][0]:
            # noinspection PyBroadException
            try:
                id = int(db.read('''SELECT ID FROM ScreenShots''')[-1][0]) + 1
            except:
                id = 1
            name = request.form['name'][:-2]
            b3id = int(request.form['b3id'])
            connections = int(request.form['connections'])
            aliases = request.form['aliases']
            guid = request.form['guid']
            penalties = int(request.form['penalties'])
            ip = request.form['ip']
            score = request.form['score']
            # noinspection PyBroadException
            try:
                with urllib.request.urlopen("https://ipinfo.io/{}/json".format(ip)) as url:
                    data = json.loads(url.read().decode())
                    address = '{}, {}'.format(data['city'], data['country']).strip(', ')
            except:
                address = 'Not Found'
            f = request.files['ss']

            s3_client.upload_fileobj(f, os.getenv("BUCKET_NAME").strip(),
                                     'MrDetective/screenshots/{}.jpg'.format(id),
                                     ExtraArgs={'ACL': 'public-read'})

            db.write('''INSERT INTO ScreenShots (Name,B3ID,Connections,Aliases,GUID,Address,IP,Penalties,Score,
                        Timestamp) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''', name, b3id, connections,
                     aliases, guid, address, ip, penalties, score, int(time.time()))
            db.close()
            return jsonify('Got IT')
    except Exception as e:
        LOG.exception(e)
        return jsonify('Something Went Wrong')


if __name__ == '__main__':
    app.run(host="0.0.0.0")
