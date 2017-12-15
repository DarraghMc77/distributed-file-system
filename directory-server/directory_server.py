from __future__ import print_function
import json
import sys
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import string
import requests
import datetime
from functools import wraps

FILE_DIR_PATH = "./files/"
IP = "10.6.64.197"
SERVERS = [9000, 9001]

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

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'admin' and password == 'secret'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route("/get_file")
def get_file():
    file_path = request.args.get('file')
    print(file_path, file=sys.stderr)
    # Find server which contains the file
    file = Files.query.get(file_path)
    print(file, file=sys.stderr)
    if file:
        query_params = {"file": file_path}
        file_lock = requests.get("http://{}:{}/get_file".format(IP, file.port), params=query_params)
        if file_lock.status_code == 200:
            print("File found", file=sys.stderr)
            query_params = {"file": file_path}
            response = requests.get("http://{}:{}/get_file".format(IP, file.port), params=query_params)
            file_json = json.loads(response.text)

            last_modified = Files.query.get(file_path).last_modified
            file_json['timestamp'] = str(last_modified)

            json_file = json.dumps(file_json)
            return json_file, 200
    else:
        return "File not found", 404

@app.route("/update_file", methods=['POST'])
def update_file():
    file = request.get_json()
    file_path = file['file']
    file_contents = file['contents']
    print("Creating new file", file=sys.stderr)

    # Check if file exists
    file = Files.query.get(file_path)
    if file:
        query_params = {"file": file_path}
        file_lock = requests.get("http://{}:{}/get_file".format(IP, file.port), params=query_params)
        if file_lock.status_code == 200:
            print("Updating file", file=sys.stderr)
            # Update file
            file.last_modified = datetime.datetime.now()
            db.session.commit()

            json_file = json.dumps({'file': file_path, 'contents': file_contents})
            headers = {'content-type': 'application/json'}
            response = requests.post("http://{}:{}/update_file".format(IP, file.port), data=json_file, headers=headers)
            return "File updated", 200
        else:
            return "File is locked", 401
    else:
        print("Creating new file", file=sys.stderr)
        # Create new file

        # directories beginning with a - m are assigned to server 9000
        # directories beginning with n - z are assigned to server 9001
        if string.ascii_lowercase.index(file_path[0]) < 13:
            port_num = SERVERS[0]
        else:
            port_num = SERVERS[1]

        file_db = Files(file=file_path, port=port_num, last_modified=datetime.datetime.now())
        db.session.add(file_db)
        db.session.commit()

        json_file = json.dumps({'file': file_path, 'contents': file_contents})
        headers = {'content-type': 'application/json'}
        response = requests.post("http://{}:{}/update_file".format(IP, port_num), data=json_file,
                                 headers=headers)

        return "File Created", 200

@app.route("/delete_file", methods=['DELETE'])
def delete_file():
    file_path = request.args.get('file')

    # Find server which contains the file
    file = Files.query.get(file_path)

    if file:
        query_params = {"file": file_path}
        file_lock = requests.get("http://{}:{}/get_file".format(IP, file.port), params=query_params)
        if file_lock.status_code == 200:
            # Delete from directory
            file.delete()
            db.session.commit()

            # Delete from file server
            query_params = {"file": file.file}
            response = requests.delete("http://{}:{}/delete_file".format(IP, file.port), params=query_params)
            return "File Deleted", 200
        else:
            return "File is locked", 401
    else:
        return "File not found", 404

@app.route("/get_file_timestamp")
def get_file_timestamp():
    file_path = request.args.get('file')
    print(file_path, file=sys.stderr)
    # Find server which contains the file
    file = Files.query.get(file_path)
    print(file, file=sys.stderr)
    if file:
        return str(file.last_modified), 200
    else:
        return "File not found", 404


def main():
    # db.drop_all()
    db.create_all()
    db.session.commit()

    app.run(host='0.0.0.0', port=80, debug=True)

if __name__ == "__main__":
    main()