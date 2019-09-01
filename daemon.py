import socket
from _thread import start_new_thread
from pickle import dumps, loads
from helper import Database, LOG, recv_msg
import urllib.request
import time
import json
import os
from requests_toolbelt import MultipartEncoder
import requests

# dataDict = {'Address': None, 'SecretKey': None, 'Data': None}
Outgoing = []
Incoming = []


def transmitter(connection, ip):
    while True:
        try:
            for transmission in Outgoing:
                if transmission['Address'] == ip:
                    connection.send(dumps(transmission['Data']), 2)
                    Outgoing.remove(transmission)

        except Exception as er:
            LOG.exception(er)
            connection.close()
            break


def listener(connection):
    while True:
        try:
            data = recv_msg(connection)
            data = loads(data, encoding='latin1')
            # LOG.info(data)
            if data['Action'] == 'WebAuth':
                authorized(data['Data'])
            elif data['Action'] == 'SS_Submit':
                submit_ss(data)
            elif data['Action'] == 'Check Connection':
                continue
            elif data['Action'] == 'Send':
                Outgoing.append(data)
            else:
                Incoming.append(data)
        except Exception as er:
            LOG.exception(er)
            connection.close()
            break


def start_daemon():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        s.bind(('188.166.187.32', 28959))
    except socket.error as e:
        LOG.exception(str(e))
        return False

    s.listen(5)
    LOG.info('Waiting for a connection.')
    while True:
        try:
            conn, addr = s.accept()
            DB = Database('MrDetective')
            data = DB.read("SELECT * FROM ClientInfos WHERE IP = (?)", addr[0])
            DB.close()
            if data:
                LOG.debug('connected to: {}:{}'.format(addr[0], addr[1]))
                start_new_thread(listener, (conn,))
                start_new_thread(transmitter, (conn, addr[0]))
            else:
                LOG.info('Connection Rejected: {}:{}'.format(addr[0], addr[1]))
                s.close()
        except Exception as e:
            LOG.exception(e)


def authorized(transmission):
    try:
        db = Database(transmission['ClanTag'])
        b3id = int(transmission['B3ID'])
        guid = transmission['GUID']
        level = int(transmission['Level'])
        permissions = ''
        if level >= 1:
            permissions += 'getss, '
        if level >= 32:
            permissions += 'ban, '
        if level >= 64:
            permissions += 'train, delss, '
        if level >= 128:
            permissions += 'add_admin, remove_admin'
        permissions = permissions.strip(', ')
        authkey = transmission['authkey']
        db.write('''UPDATE users SET b3id = (?), guid = (?),Permissions = (?), authkey = (?)
                    WHERE authkey = (?)''', b3id, guid, permissions, None, authkey)
        db.close()
    except Exception as e:
        LOG.exception(e)


# noinspection PyBroadException
def submit_ss(transmission):
    try:
        clan = transmission['ClanTag']
        db = Database(clan)
        try:
            id = int(db.read('''SELECT ID FROM ScreenShots''')[-1][0]) + 1
        except:
            id = 1
        transmission = transmission['Data']
        name = transmission['Name'][:-2]
        b3id = int(transmission['B3ID'])
        connections = int(transmission['Connections'])
        aliases = transmission['Aliases']
        guid = transmission['GUID']
        penalties = int(transmission['Penalties'])
        ip = transmission['IP']
        try:
            with urllib.request.urlopen("https://ipinfo.io/{}/json".format(ip)) as url:
                data = json.loads(url.read().decode())
                address = '{}, {}'.format(data['city'], data['country']).strip(', ')
        except:
            address = 'Not Found'

        if not os.path.exists('static/screenshots/{}'.format(clan)):
            os.makedirs('static/screenshots/{}'.format(clan))

        with open('static/screenshots/{}/{}.jpg'.format(clan, id), 'wb') as f:
            f.write(transmission['Screenshot'].encode('latin1'))

        ss = ('filename', open('static/screenshots/{}/{}.jpg'.format(clan, id), 'rb'), 'text/plain')
        try:
            m = MultipartEncoder(fields={'file': ss})
            score = json.loads(requests.post('http://5.189.191.203:5000/MrDetective/Predict/', data=m,
                                             headers={'Content-Type': m.content_type}).text)
            score = str(round(float(score['prediction']), 2))
        except:
            score = str(-1)

        db.write('''INSERT INTO ScreenShots (Name,B3ID,Connections,Aliases,GUID,Address,IP,Penalties,Score,
                    Timestamp) VALUES (?,?,?,?,?,?,?,?,?,?)''', name, b3id, connections,
                 aliases, guid, address, ip, penalties, score, int(time.time()))
        db.close()
        LOG.info('{}, {}, {}, {}, {}, {}, {}, {}, {}, {}'.format(name, b3id, connections, aliases, guid, address, ip,
                                                                 penalties, score, int(time.time())))
    except Exception as e:
        LOG.exception(e)


if __name__ == '__main__':
    start_daemon()
