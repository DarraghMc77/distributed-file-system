from __future__ import print_function
import json
import sys
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import requests
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lock.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

IP = os.getenv('SERVER_IP')
AUTH_PORT = 5005

class Lock(db.Model):
    file = db.Column(db.String(64), index=True, primary_key=True)
    locked = db.Column(db.Integer, index=True)

    def __repr__(self):
        return 'File: %r, Locked: &d' % (self.file, self.locked)

def check_authentication(token):
    json_token = json.dumps({'token': token})
    headers = {'content-type': 'application/json'}
    response = requests.put("http://{}:{}/authenticate".format(IP, AUTH_PORT), data=json_token,
                                 headers=headers)
    return response.status_code == 200

@app.route("/lock_file", methods=['PUT'])
def lock_file():
    # verify user is logged in
    if not check_authentication(request.headers.get('Authorization')):
        return "Unauthorized", 401

    file_path = request.args.get('file')
    file = Lock.query.get(file_path)
    if file:
        if file.locked:
            return "File already locked", 200
        else:
            file.locked = 1
            db.session.commit()
            return "File has been locked", 200
    else:
        file_db = Lock(file=file_path, locked=1)
        db.session.add(file_db)
        db.session.commit()
        return "File has been locked", 200

@app.route("/unlock_file", methods=['PUT'])
def unlock_file():
    if not check_authentication(request.headers.get('Authorization')):
        return "Unauthorized", 401

    file_path = request.args.get('file')
    file = Lock.query.get(file_path)
    if file:
        print("File found", file=sys.stderr)
        if file.locked:
            file.locked = 0
            db.session.commit()
            return "File has been unlocked", 200
        else:
            return "File is already unlocked", 400
    else:
        return "File is already unlocked", 400

@app.route("/is_file_locked")
def check_lock():
    file_path = request.args.get('file')
    file = Lock.query.get(file_path)

    if file:
        if file.locked == 1:
            return "file is locked", 400
        else:
            return "File is unlocked", 200
    else:
        return "File is unlocked", 200

def main():
    db.drop_all()
    db.create_all()
    db.session.commit()

    app.run(host='0.0.0.0', port=80, debug=True)

if __name__ == "__main__":
    main()