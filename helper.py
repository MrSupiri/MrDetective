import gc
import os
import logging
import struct
import psycopg2


class Database:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                database=os.getenv('PG_DATABASE').strip(),
                user=os.getenv('PG_USERNAME').strip(),
                password=os.getenv('PG_PASSWORD').strip(),
                host=os.getenv('PG_HOST').strip(),
                port=os.getenv('PG_PORT').strip())

            self.c = self.conn.cursor()
        except Exception as e:
            LOG.exception(e)

    def read(self, query, *pars):
        try:
            self.c.execute(query, pars)
            return self.c.fetchall()
        except Exception as e:
            LOG.exception(e)

    def write(self, query, *pars):
        try:
            self.c.execute(query, pars)
            self.conn.commit()
            return query
        except Exception as e:
            LOG.exception(e)

    def close(self):
        self.c.close()
        self.conn.close()
        gc.collect()


class Logger(object):
    def __init__(self):
        try:
            self.buildFailed = False
            os.chdir(os.path.dirname(os.path.abspath(__file__)))
            if not os.path.exists('data'):
                os.makedirs('data')
            file_name = "data/MrDetective.log"

            logFormatter = logging.Formatter(
                fmt='%(asctime)-10s %(levelname)-10s: %(module)s:%(lineno)-d -  %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')

            self.log = logging.getLogger()
            self.log.setLevel(10)

            fileHandler = logging.FileHandler(file_name)
            fileHandler.setFormatter(logFormatter)
            self.log.addHandler(fileHandler)
            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(logFormatter)
            self.log.addHandler(consoleHandler)
        except Exception as e:
            self.log.exception(e)


LOG = Logger().log


def send_msg(sock, msg):
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>I', len(msg)) + msg
    sock.sendall(msg)


def recv_msg(sock):
    # Read message length and unpack it into an integer
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recvall(sock, msglen)


def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data
