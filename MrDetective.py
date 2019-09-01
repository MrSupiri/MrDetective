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
import json as js
import os


app = Flask(__name__)
app.secret_key = '\xaco(#\x0e\xd6u\xd0\xe6\x04)\xd2~bk\x1a\xea\x11(\x87Kf\xb3=\x14\xc9\xe2\x9e\x05\xba\xa1{\xb5'



# session['permission'] = ban, train, unban, getss, delss, add_admin, remove_admin
def check404(clan):
    DB = Database('MrDetective')
    clans = DB.read('SELECT "Clan Tag" FROM ClientInfos')
    clans = [i[0] for i in clans]
    DB.close()
    if 'clan' in session and session['clan'] != clan:
        print(session['clan'])
        session.clear()
        flash("You were forced to logged out!")
    if clan not in clans:
        session.clear()
        flash("404 Clan was not Found")
        flash("You were Redirect to a Random Page")
        return random.choice(clans)
    else:
        return False


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


@app.route('/', methods=['GET'])
def noclan():
    redirect_clan = check404(None)
    if redirect_clan:
        return redirect(url_for('home', clan=redirect_clan))
    else:
        DB = Database('MrDetective')
        clans = DB.read('SELECT "Clan Tag" FROM ClientInfos')
        clans = [i[0] for i in clans]
        DB.close()
        return redirect(url_for('home', clan=random.choice(clans)))
        

@app.route('/<clan>/auth/', methods=["GET","POST"])
def auth(clan):
    redirect_clan = check404(clan)
    if redirect_clan:
        redirect(url_for('home', clan=redirect_clan))
    try:
        db = Database(clan)
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
            db.write('''UPDATE users SET B3ID = (?), GUID = (?) ,Permissions = (?), authkey = (?) WHERE authkey = (?)''',b3id,guid,power,None,authkey)
            db.close()
        return 'ok'
    except Exception as e:
        LOG.exception(e)
        return 'error'


@app.route('/<clan>/', methods=["POST", 'GET'])
def home(clan):
    if str(clan).endswith('.ico'):
        return abort(404)
    redirect_clan = check404(clan)
    if redirect_clan:
        return redirect(url_for('home', clan=redirect_clan))
    try:
        if 'authkey' in session and session['authkey'] is not None:
            flash("Welcome ! It's look like you are new to here when you visit the Black Assassins Server type"
                  " !webauth {} to complete the registration".format(session['authkey']))
        db = Database(clan)
        session['last_ss'] = int(db.read('SELECT ID FROM screenshots ORDER BY ID DESC LIMIT 1')[0][0])
        ss = db.read('SELECT * FROM screenshots WHERE ID <= (?) ORDER BY ID DESC LIMIT 27', session['last_ss'])
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
            return render_template('home.html', ss=ss, clan=clan)
        else:
            return render_template('home.html', ss=ss, clan=clan)
    except Exception as e:
        LOG.exception(e)
        return render_template('home.html', ss=[], clan='')


@app.route('/<clan>/load/')
def load(clan):
    check404(clan)
    db = Database(clan)
    session['last_ss'] -= 27
    if session['last_ss'] <= 0:
        session['last_ss'] = int(db.read('SELECT ID FROM screenshots ORDER BY ID DESC LIMIT 1')[0][0])
    ss = db.read('SELECT * FROM screenshots WHERE ID <= (?) ORDER BY ID DESC LIMIT 27', session['last_ss'])
    db.close()
    ss_new = []
    for s in ss:
        s = list(s)
        s[-1] = datetime.fromtimestamp(s[-1])
        s[1] = escape(s[1])
        s[4] = escape(str(s[4])[:90].strip(',').strip(' '))
        ss_new.append(s)
    ss = ss_new
    return render_template('card_generator.html', ss=ss, clan=clan)


@app.route('/<clan>/ss/')
def reroute(clan):
    redirect_clan = check404(clan)
    if redirect_clan:
        redirect(url_for('home', clan=redirect_clan))
    return redirect(url_for('imageview', clan=clan, ssid=1))


@app.route('/<clan>/ss/<ssid>/')
def imageview(clan, ssid):
    redirect_clan = check404(clan)
    if redirect_clan:
        return redirect(url_for('home', clan=redirect_clan))
    db = Database(clan)
    ss = db.read('SELECT * FROM screenshots WHERE ID = (?) ORDER BY ID DESC LIMIT 1', ssid)
    db.close()
    try:
        return render_template("imageview.html", data=ss, clan=clan)
    except Exception as e:
        LOG.exception(e)
        flash('ScreenShot Not Found')
        return redirect(url_for('home', clan=clan))


@app.route('/<clan>/login/', methods=["POST"])
def login(clan):
    redirect_clan = check404(clan)
    if redirect_clan:
        return redirect(url_for('home', clan=redirect_clan))
    try:
        if request.method == "POST":
            db = Database(clan)
            username = request.form['username'].lower()
            users = db.read('SELECT Username,password,AuthKey,GUID,B3ID,Permissions FROM users WHERE username = (?)',
                            username)
            if not users:
                users = db.read('''SELECT Username,password,AuthKey,GUID,B3ID,Permissions FROM users WHERE
                                Email = (?)''', username)
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
                session['clan'] = clan
                flash('Welcome {}!'.format(users[0][0].title()))
                return redirect(request.referrer)
            else:
                flash('Invalid credentials. Try Again.')
                return redirect(request.referrer)
    except Exception as e:
        LOG.exception(e)
        return redirect(request.referrer)


@app.route('/<clan>/register/', methods=["POST"])
def register(clan):
    redirect_clan = check404(clan)
    if redirect_clan:
        return redirect(url_for('home', clan=redirect_clan))
    try:
        if request.method == "POST":
            db = Database(clan)
            displayname = request.form['name']
            username = str(request.form['regusername']).lower()
            password = sha256_crypt.encrypt(str(request.form['regpassword']))
            email = request.form['email']
            AuthKey = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            x = db.read("SELECT * FROM users WHERE Username = (?)", username)
            y = db.read("SELECT * FROM users WHERE Email = (?)", email)
            if x:
                flash('Username Already in Use')
                return redirect(request.referrer)
            if y:
                flash('Your Email is already Registered')
                return redirect(request.referrer)
            db.write('''INSERT INTO users(Name,Username,Password,Email,AuthKey) VALUES(?,?,?,?,?)''', displayname,
                     username, password, email, AuthKey)
            db.close()
            flash('You Have Successfully Registered !')
            return redirect(request.referrer)
    except Exception as e:
        LOG.exception(e)
        return redirect(url_for(home, clan=clan))


@app.route('/<clan>/logout/')
@login_required
def logout(clan):
    redirect_clan = check404(clan)
    if redirect_clan:
        return redirect(url_for('home', clan=redirect_clan))
    try:
        session.clear()
        flash("You have been logged out!")
        return redirect(request.referrer)
    except Exception as e:
        LOG.exception(e)
        return render_template("home.html")


@app.route('/<clan>/ban/<ssid>')
@permission_ban
def ban_player(clan, ssid):
    redirect_clan = check404(clan)
    if redirect_clan:
        return redirect(url_for('home', clan=redirect_clan))
    try:
        db = Database(clan)
        id = str(db.read('''SELECT B3ID from ScreenShots where ID = (?)''', ssid)[0][0])
        
        m = MultipartEncoder(
            fields={"b3id": str(session['b3id']), "cmd": 'ban', "args": '@'+id,"args2": '^3WallHacker^0|^1Proof- ss.supiritech.tk/{}/ss/{}'.format(clan, ssid), "secretkey": db.read('SELECT secretkey from server_info')[0][0]}
        )
        ip,port,url = db.read('SELECT b3_ip,b3_port,b3_url from server_info')[0]
        LOG.error('http://{}:{}/{}'.format(ip,port,url))
        r = str(requests.post('http://{}:{}/{}'.format(ip,port,url), data=m, headers={'Content-Type': m.content_type}).text)
        if 'true' in str(r):
            data = db.write('''UPDATE ScreenShots SET banned = (?) WHERE ID = (?)''',session['username'],str(ssid))
            flash('Player Was Successfully Banned')
        else:
            flash('There was a error while banning the player, Try Again in Bit !')
            flash('Make Sure You are Connected to Server Before Banning Again')
        db.close()
        return redirect(request.referrer)
    except:
        flash('Something Went Wrong')
        return redirect(request.referrer)


# def ban_player(clan, ssid):
#     redirect_clan = check404(clan)
#     if redirect_clan:
#         return redirect(url_for('home', clan=redirect_clan))
#     try:
#         db = Database(clan)
#         id = str(db.read('''SELECT B3ID FROM screenshots WHERE ID = (?)''', ssid)[0][0])
#         IP = Database('MrDetective').read('SELECT IP FROM ClientInfos WHERE "Clan Tag"=?', clan)[0][0]
#         dataDict = {'client': session['b3id'], 'sclient': id, 'action': 'ban',
#                     'reason': '^3Mistaken SS^0|^1ss.supiritech.tk/{}/ss/{}'.format(clan, ssid)}
#         Key = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
#         Outgoing.append({'Address': IP, 'Data': dataDict, 'Key': Key})
#         i = 0
#         success = False
#         feedback = "B3 Didn't Response to your Ban Request"
#         while i < 30:
#             i += 1
#             time.sleep(1)
#             for transmission in Incoming:
#                 if transmission['ClanTag'] == clan and transmission['Data'] == Key:
#                     i = 31
#                     if transmission['Info']:
#                         success = True
#                         feedback = transmission['Info']
#                         Outgoing.remove(transmission)
#                     else:
#                         success = False
#                         feedback = transmission['Error']
#                         Outgoing.remove(transmission)
#                     break
#         if success:
#             db.write('''UPDATE screenshots SET Banned = (?) WHERE ID = (?)''', session['username'], ssid)
#             flash(feedback)
#         else:
#             flash(feedback)
#         db.close()
#         return redirect(request.referrer)
#     except Exception as e:
#         LOG.exception(e)
#         flash('Something Went Wrong')
#         return redirect(request.referrer)


@app.route('/<clan>/unban/<ssid>')
@permission_ban
def unban_player(clan, ssid):
    redirect_clan = check404(clan)
    if redirect_clan:
        return redirect(url_for('home', clan=redirect_clan))
    try:
        db = Database(clan)
        db.write('''UPDATE screenshots SET Banned = (?) WHERE ID = (?)''', None, ssid)
        flash("B3 Didn't Response to your Ban Request")
        flash("You have to Manually unban the Player via b3")
        db.close()
        return redirect(request.referrer)
    except Exception as e:
        LOG.exception(e)
        flash('Something Went Wrong')
        return redirect(request.referrer)


@app.route('/<clan>/submit_ss/', methods=["POST"])
def submit_ss(clan):
    try:
        db = Database(clan)
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
            if not os.path.exists('static/screenshots/{}'.format(clan)):
                os.makedirs('static/screenshots/{}'.format(clan))
            f.save('static/screenshots/{}/{}.jpg'.format(clan, id))

            db.write('''INSERT INTO ScreenShots (Name,B3ID,Connections,Aliases,GUID,Address,IP,Penalties,Score,
                        Timestamp) VALUES (?,?,?,?,?,?,?,?,?,?)''', name, b3id, connections,
                     aliases, guid, address, ip, penalties, score, int(time.time()))
            db.close()
            return jsonify('Got IT')
    except Exception as e:
        LOG.exception(e)
        return jsonify('Something Went Wrong')



if __name__ == '__main__':
    app.run()
