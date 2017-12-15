import json
import requests
import sys
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

engine = create_engine('sqlite:///cached_files.db', echo=True)

Base = declarative_base()

Session = sessionmaker(bind=engine)

class CachedFile(Base):
     __tablename__ = 'files'

     file = Column(String, primary_key=True, index = True)
     file_contents = Column(String, index = True)
     last_modified = Column(DateTime, index=True)

     def __repr__(self):
        return "<File(path='%s', last_modified='%s', file_contents='%s')>" % (
                             self.file, str(self.last_modified), self.file_contents)

Base.metadata.create_all(engine)

JSON_HEADERS = {'content-type': 'application/json'}
SERVER_IP = "192.168.0.25"

FILE_PORT = "9000"
LOCK_PORT = "7000"
DIR_PORT = "8001"
AUTH_PORT = "5005"

CACHE_LIMIT = 100

FILE_DIR_PATH = "./files/"

def download_file(headers, session, file_path):
    # Check cache for file
    cache_file = session.query(CachedFile).get(file_path)
    if cache_file:
        print("File in cache")
        query_params = {"file": file_path}
        response = requests.get("http://{}:{}/get_file_timestamp".format(SERVER_IP, DIR_PORT), params=query_params, headers = headers)
        if response.status_code == 404:
            print(response.text)
            return
        if response.status_code == 401:
            print(response.text)
            return
        file_timestamp = response.text
        dir_last_modified = datetime.strptime(file_timestamp, "%Y-%m-%d %H:%M:%S.%f")
        if dir_last_modified == cache_file.last_modified:
            print("Up to date file in cache")
        else:
            query_params = {"file": file_path}
            response = requests.get("http://{}:{}/get_file".format(SERVER_IP, DIR_PORT), params=query_params, headers = headers)
            if response.status_code == 200:
                json_file = json.loads(response.text)

                # update caching db
                cache_file.last_modified = dir_last_modified
                cache_file.file_contents = json_file['contents']
                session.commit()

                print("File downloaded")
            else:
                print(response.text)
    else:
        print("File not in cache")
        query_params = {"file": file_path}
        response = requests.get("http://{}:{}/get_file".format(SERVER_IP, DIR_PORT), params=query_params, headers=headers)
        if response.status_code == 200:
            json_file = json.loads(response.text)
            last_modified = datetime.strptime(json_file['timestamp'], "%Y-%m-%d %H:%M:%S.%f")

            # LRU implementation - oldest file in cache is removed if number of rows is the max length
            cache_size = session.query(CachedFile).count()
            print(cache_size)
            if cache_size >= CACHE_LIMIT:
                lru_file = session.query(CachedFile).order_by(CachedFile.last_modified).first()
                print(lru_file)
                session.delete(lru_file)
                session.commit()

            # update caching db
            cache_file = CachedFile(file=str(file_path), last_modified=last_modified, file_contents=json_file['contents'])
            session.add(cache_file)
            session.commit()

            print("File downloaded")
        else:
            print(response.text)


def modify_file(session, file_path, file_contents):
    file = session.query(CachedFile).get(file_path)
    if file:
        file.file_content = file_contents
        file.last_modified = datetime.now()
        session.commit()
        return file
    else:
        file = CachedFile(file=file_path, file_contents=file_contents, last_modified = datetime.now())
        session.add(file)
        session.commit()
        return file

def upload_file(headers, session, file):
    json_file = json.dumps({'file': file.file, 'contents': file.file_contents, 'timestamp': str(file.last_modified)})
    response = requests.post("http://{}:{}/update_file".format(SERVER_IP, DIR_PORT), data=json_file, headers=headers)
    print(response)

def delete_file(headers, session, file_path):
    cache_file = session.query(CachedFile).get(file_path)
    if cache_file:
        session.delete(cache_file)
        session.commit()
    query_params = {"file": file_path}
    response = requests.delete("http://{}:{}/delete_file".format(SERVER_IP, DIR_PORT), params=query_params, headers=headers)
    print(response.text)

def lock_file(headers, file_path):
    query_params = {"file": file_path}
    response = requests.put("http://{}:{}/lock_file".format(SERVER_IP, LOCK_PORT), params=query_params, headers=headers)
    print(response.text)

def unlock_file(headers, file_path):
    query_params = {"file": file_path}
    response = requests.put("http://{}:{}/unlock_file".format(SERVER_IP, LOCK_PORT), params=query_params, headers=headers)
    print(response.text)

def logout(headers):
    response = requests.put("http://{}:{}/logout".format(SERVER_IP, AUTH_PORT), headers=headers)
    print(response.text)

def main():
    # Initialize database for keeping track of cached files
    session = Session()

    while True:

        # User login
        while True:
            choice = input("1. Register \n2. Login")
            print(choice)
            if choice == "1":
                user_id = input("Enter user id (Integer)")
                password = input("Enter password")
                json_user = json.dumps({'userId': user_id, 'password': password})
                response = requests.post("http://{}:{}/register".format(SERVER_IP, AUTH_PORT), data=json_user,
                                        headers=JSON_HEADERS)
                if response.status_code == 200:
                    access_token = json.loads(response.text)['token']
                    break
                else:
                    print(response.text)
                    print("Unable to register user, retry")
            elif choice == "2":
                user_id = input("Enter user id")
                password = input("Enter password")
                json_user = json.dumps({'userId': user_id, 'password': password})
                response = requests.put("http://{}:{}/login".format(SERVER_IP, AUTH_PORT), data=json_user,
                                         headers=JSON_HEADERS)
                if response.status_code == 200:
                    access_token = json.loads(response.text)['token']
                    break
                else:
                    print("Incorrect login details, retry")

        headers = {'content-type': 'application/json', 'Authorization': access_token}

        while True:
            choice = input("1. Open file \n2. Modify/Create file \n3. Delete file \n4. Lock File \n5. Unlock File \n6. Logout \n7. Close program")
            if(choice == "1"):
                file_name = input("Enter file path")
                download_file(headers, session, file_name)
            elif(choice == "2"):
                file_name = input("Enter file path")
                file_contents = input("Enter File Contents")
                file = modify_file(session, file_name, file_contents)
                entry_input = input("1. Upload modified file \n2. Return to main menu")
                if entry_input == "1":
                    upload_file(headers, session, file)
            elif(choice == "3"):
                file_name = input("Enter file path")
                delete_file(headers, session, file_name)
            elif(choice == "4"):
                file_name = input("Enter file path")
                lock_file(headers, file_name)
            elif (choice == "5"):
                file_name = input("Enter file path")
                unlock_file(headers, file_name)
            elif (choice == "6"):
                logout(headers)
                # Return to login prompt
                break
            elif(choice == "7"):
                sys.exit()

if __name__ == "__main__":
    main()