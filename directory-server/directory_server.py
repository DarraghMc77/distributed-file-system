from __future__ import print_function
import json
import sys
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import string
import requests
from datetime import datetime
import os

FILE_DIR_PATH = "./files/"
IP = os.getenv('SERVER_IP')
SERVERS = [9000, 9001]
AUTH_PORT = 5005
LOCK_PORT = 7000

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///directory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Files(db.Model):
    file = db.Column(db.String(64), index=True, primary_key=True)
    port = db.Column(db.String(64), index=True)
    last_modified = db.Column(db.DateTime, index=True)

    def __repr__(self):
        return '<File %r>' % (self.file)

def check_authentication(token):
    json_token = json.dumps({'token': token})
    headers = {'content-type': 'application/json'}
    response = requests.put("http://{}:{}/authenticate".format(IP, AUTH_PORT), data=json_token,
                                 headers=headers)
    return response.status_code == 200

@app.route("/get_file")
def get_file():
    # verify user is logged in
    if not check_authentication(request.headers.get('Authorization')):
        return "Unauthorized", 401

    file_path = request.args.get('file')

    # Find server which contains the file
    file = Files.query.get(file_path)
    print(file, file=sys.stderr)
    if file:
        query_params = {"file": file_path}
        # check if file is locked
        file_lock = requests.get("http://{}:{}/is_file_locked".format(IP, LOCK_PORT), params=query_params)
        if file_lock.status_code == 200:
            query_params = {"file": file_path}
            response = requests.get("http://{}:{}/get_file".format(IP, file.port), params=query_params)
            file_json = json.loads(response.text)

            last_modified = Files.query.get(file_path).last_modified
            file_json['timestamp'] = str(last_modified)

            json_file = json.dumps(file_json)
            return json_file, 200
        else:
            return "File is locked", 401
    else:
        return "File not found", 404

@app.route("/update_file", methods=['POST'])
def update_file():
    # verify user is logged in
    if not check_authentication(request.headers.get('Authorization')):
        return "Unauthorized", 401

    file = request.get_json()
    file_path = file['file']
    file_contents = file['contents']
    file_timestamp = datetime.strptime(file['timestamp'], "%Y-%m-%d %H:%M:%S.%f")

    # Check if file exists
    file = Files.query.get(file_path)
    if file:
        query_params = {"file": file_path}
        file_lock = requests.get("http://{}:{}/is_file_locked".format(IP, LOCK_PORT), params=query_params)
        if file_lock.status_code == 200:
            print("Updating file", file=sys.stderr)
            # Update file
            file.last_modified = file_timestamp
            db.session.commit()

            json_file = json.dumps({'file': file_path, 'contents': file_contents})
            headers = {'content-type': 'application/json'}
            response = requests.post("http://{}:{}/update_file".format(IP, file.port), data=json_file, headers=headers)
            return "File updated", 200
        else:
            return "File is locked", 401
    else:
        print("Creating new file", file=sys.stderr)

        # directories beginning with a - m are assigned to server 9000
        # directories beginning with n - z are assigned to server 9001
        if string.ascii_lowercase.index(file_path[0]) < 13:
            port_num = SERVERS[0]
        else:
            port_num = SERVERS[1]

        file_db = Files(file=file_path, port=port_num, last_modified=file_timestamp)
        db.session.add(file_db)
        db.session.commit()

        json_file = json.dumps({'file': file_path, 'contents': file_contents})
        headers = {'content-type': 'application/json'}
        response = requests.post("http://{}:{}/update_file".format(IP, port_num), data=json_file,
                                 headers=headers)

        return response.text, 200

@app.route("/delete_file", methods=['DELETE'])
def delete_file():
    # verify user is logged in
    if not check_authentication(request.headers.get('Authorization')):
        return "Unauthorized", 401

    file_path = request.args.get('file')
    # Find server which contains the file
    file = Files.query.get(file_path)

    if file:
        query_params = {"file": file_path}
        file_lock = requests.get("http://{}:{}/is_file_locked".format(IP, LOCK_PORT), params=query_params)
        if file_lock.status_code == 200:
            # Delete from directory
            db.session.delete(file)
            db.session.commit()

            # Delete from file server
            query_params = {"file": file.file}
            response = requests.delete("http://{}:{}/delete_file".format(IP, file.port), params=query_params)
            return response.text, 200
        else:
            return "File is locked", 401
    else:
        return "File not found", 404

@app.route("/get_file_timestamp")
def get_file_timestamp():
    # verify user is logged in
    if not check_authentication(request.headers.get('Authorization')):
        return "Unauthorized", 401
    file_path = request.args.get('file')
    file = Files.query.get(file_path)
    if file:
        return str(file.last_modified), 200
    else:
        return "File not found", 404


def main():
    db.drop_all()
    db.create_all()
    db.session.commit()

    app.run(host='0.0.0.0', port=80, debug=True)

if __name__ == "__main__":
    main()