# Distributed File System
Distributed file system project for module CS7NS1, Scalable Computing, based on the AFS model and written in Python using the Flask framework. Features implemented are:
+ Distributed Transparent File Access
+ Directory Service
+ Caching
+ Lock Service
+ Security

### Usage
To build docker services specified in docker-compose.yml file:
```
docker-compose build
```
To run services:
```
docker-compose up
```
Repeat this for each service.

## File Server
The file server provides the user with access to the files stored on that server. Functionality of the file server I have implemented includes:
+ get (download a file from the file server)
+ update (upload/modify a file on the file server)
+ delete (delete a file from the file server)

## Client
When client is started the user is first prompted with a menu of actions they can complete, this menu includes:
+ open (downloads file for use)
+ close (uploads file to file server)
+ edit (make changes to the file)
+ delete (deletes file from file server)
+ lock (locks file)
+ unlock (unlocks file)

## Caching
As this system uses a download/upload approach, caching is implemented client side. When a file is downloaded from the file server it is immediately placed in the clients caching db. If a file is then modified or requested for download, the cache is first checked to see if it contains that file. If the cache contains the file, the time the file was last modified on the file server is requested and compared to the time the file in cache was stored. If the times are the same then the file in cache is used, else the file is downloaded from the file server. A Least Recently Used policy was implemented by querying the caching db for the oldest entry when a new file is being added. The oldest entry is then removed from the db and the new file is added.

## Directory Service
The directory service acts as a proxy between the client and file servers. It determines which server to upload the file to when the client creates a new file. It also locates the server on which each file is located when requested by the client and downloads/modifies/deletes a file based on the clients request. The location of each file is stored in a SQLite database.

## Lock Service
This locking server functionality includes, locking a file, unlocking a file and the ability to check if a file is locked. The locking server is implemented by simply keeping a database of files that are locked. When a user tries to download or modify a file, the locking server is queried by the directory service to see if the file being downloaded is listed as being locked.

## Security
I have implemented a simple token based Authentication service. Access to the directory service is restricted to users with valid authorization tokens.
Functionality of the authentication server includes:
+ register - A randomly generated salt using bcrypt is generated and is prepended to the users password, this salt + password is then hashed using the argon2 encryption algorithm. The user id, salt and hashed password is then stored in a database and an authorization token is returned to the user for access to the file services. This authorization token is then stored in a db along with an exiry date.
+ login - The users salt is retrieved from the db and is prepended to the inputted password, this is then compared with the hashed password stored in the db. If the login details are valid an authorization token is returned to the user.
+ logout - Removes the authorization token from the db containing valid tokens.
+ authenticate - Queries the authentication token db to check whether token in request is valid.
