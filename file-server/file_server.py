from __future__ import print_function
from flask import Flask, request
import json
import sys
import os

FILE_DIR_PATH = "./files/"

app = Flask(__name__)

@app.route("/get_file")
def get_file():
    file = request.args.get('file').split("/", 1)
    print(file)
    file_name = file[1]
    file_dir = file[0]
    try:
        file = open(FILE_DIR_PATH + file_name, "r")
        file_contents = file.read()
        response = json.dumps({'file': file_dir + "/" + file_name, 'contents': file_contents})
        return response, 200
    except Exception as e:
        return "File not found", 404

@app.route("/update_file", methods=['POST'])
def create_file():
    json_file = request.get_json()
    print(json_file, file=sys.stderr)
    file = request.get_json()['file'].split("/", 1)
    file_name = file[1]
    file_dir = file[0]
    contents = json_file['contents']
    file = open(FILE_DIR_PATH + file_name, "w+")
    file.write(contents)
    file.close()
    return "File Created", 200

@app.route("/delete_file", methods=['DELETE'])
def delete_file():
    file = request.args.get('file').split("/", 1)
    file_name = file[1]
    file_dir = file[0]
    os.remove(FILE_DIR_PATH + file_name)
    return "File Deleted", 200

def main():
    app.run(host='0.0.0.0', port=80, debug=True)

if __name__ == "__main__":
    main()