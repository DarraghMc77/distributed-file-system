from __future__ import print_function
import json
import sys
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import string
import requests


# 10.6.70.175:8001/get_file

FILE_DIR_PATH = "./files/"
FILE_SERVER_IP = "10.6.70.175"
SERVERS = [9000, 9001]


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///directory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)


# TODO: Move to models.py file and fix docker
class Files(db.Model):
    file = db.Column(db.String(64), index=True)
    port = db.Column(db.String(64), index=True)

    def __repr__(self):
        return '<File %r>' % (self.file)


@app.route("/get_file")
def get_file():
    file_path = request.args.get('file')

    # Find server which contains the file
    files = Files.query.filter_by(file=file_path).all()

    if files:
        print("File found", file=sys.stderr)
        query_params = {"name": file_path}
        response = requests.get("http://{}:{}/get_file".format(FILE_SERVER_IP, files[0].port), params=query_params)
        return response.text, 200
    else:
        return "File not found", 400

@app.route("/create_file", methods=['POST'])
def create_file():
    file = request.get_json()
    file_path = file['file']
    file_contents = file['contents']

    # Check if file exists
    files = Files.query.filter_by(file=file_path).all()
    if files:
        print("Updating file", file=sys.stderr)
        file = files[0]
        # Update file
        json_file = json.dumps({'name': file_path, 'contents': file_contents})
        headers = {'content-type': 'application/json'}
        response = requests.post("http://{}:{}/create_file".format(FILE_SERVER_IP, file.port), data=json_file, headers=headers)
        return "File updated", 200
    else:
        print("Creating new file", file=sys.stderr)
        # Create new file

        # directories beginning with a - m are assigned to server 9000
        # directories beginning with n - z are assigned to server 9001
        if string.ascii_lowercase.index(file_path[0]) < 13:
            port_num = SERVERS[0]
        else:
            port_num = SERVERS[1]

        file_db = Files(file=file_path, port=port_num)
        db.session.add(file_db)
        db.session.commit()

        json_file = json.dumps({'name': file_path, 'contents': file_contents})
        headers = {'content-type': 'application/json'}
        response = requests.post("http://{}:{}/create_file".format(FILE_SERVER_IP, port_num), data=json_file,
                                 headers=headers)

        return "File Created", 200

@app.route("/delete_file", methods=['DELETE'])
def delete_file():
    file_name = request.args.get('name')
    print(Files.query.filter_by(file = file_name), file=sys.stderr)
    return "test", 200


def main():
    db.drop_all()
    db.create_all()
    db.session.commit()

    app.run(host='0.0.0.0', port=80, debug=True)

if __name__ == "__main__":
    main()