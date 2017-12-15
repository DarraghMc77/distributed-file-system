from __future__ import print_function
from flask import Flask, request
import json
import os

FILE_DIR_PATH = "./files/"

app = Flask(__name__)

@app.route("/get_file")
def get_file():
    file_path = request.args.get('file')
    try:
        file = open(FILE_DIR_PATH + file_path, "r")
        file_contents = file.read()
        response = json.dumps({'file': file_path, 'contents': file_contents})
        return response, 200
    except Exception as e:
        return "File not found", 404

@app.route("/update_file", methods=['POST'])
def create_file():
    json_file = request.get_json()
    file_path = request.get_json()['file']
    if not os.path.exists(os.path.dirname(FILE_DIR_PATH + file_path)):
        print("creating directory")
        os.makedirs(os.path.dirname(FILE_DIR_PATH + file_path))
    contents = json_file['contents']
    file = open(FILE_DIR_PATH + file_path, "w+")
    file.write(contents)
    file.close()
    return "File Created", 200

@app.route("/delete_file", methods=['DELETE'])
def delete_file():
    file_path = request.args.get('file')
    os.remove(FILE_DIR_PATH + file_path)
    return "File Deleted", 200

def main():
    app.run(host='0.0.0.0', port=80, debug=True)

if __name__ == "__main__":
    main()