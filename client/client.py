import json
import requests
import sys

FILE_SERVER_URL = "http://10.6.69.232:8000/"

def main():
    while True:
        choice = input("1. Download file \n2. Edit file \n3. Delete file \n4. Close program")
        if(choice == "1"):
            file_name = input("Enter name of file")
            query_params = {"name": file_name}
            response = requests.get(FILE_SERVER_URL + "get_file", params=query_params)
            print(json.loads(response.text))
        elif(choice == "2"):
            file_name = input("Enter name of file")
            file_contents = input("Enter File Contents")
            json_file = json.dumps({'name': file_name, 'contents': file_contents})
            headers = {'content-type': 'application/json'}
            response = requests.post(FILE_SERVER_URL + "create_file", data=json_file, headers=headers)
            print(response)
        elif(choice == "3"):
            file_name = input("Enter name of file")
            query_params = {"name": file_name}
            response = requests.delete(FILE_SERVER_URL + "delete_file", params=query_params)
            print(response)
        elif(choice == "4"):
            sys.exit()

if __name__ == "__main__":
    main()