from __future__ import print_function
import json
import sys
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import flask_argon2
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///authentication.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Users(db.Model):
    user_id = db.Column(db.Integer, index=True, primary_key=True)
    password = db.Column(db.String(256), index=True)
    salt = db.Column(db.String(256), index=True)

    def __repr__(self):
        return '<User %r>' % (self.userId)

class AccessTokens(db.Model):
    token = db.Column(db.String(64), index=True, primary_key=True)
    expiry = db.Column(db.DateTime, index=True)

    def __repr__(self):
        return '<token %r>' % (self.token)


@app.route("/login", methods=['PUT'])
def login():
    json_user = request.get_json()
    user_id = json_user['userId']
    password = json_user['password']

    user = Users.query.get(user_id)
    if user:
        if flask_argon2.check_password_hash(user.password, user.salt.decode("utf-8") + password):
            token = secrets.token_hex(16)
            token_db = AccessTokens(token=token, expiry = (datetime.now() + timedelta(days=2)))
            db.session.add(token_db)
            db.session.commit()
            json_token = json.dumps({'token': token})
            return json_token, 200
        else:
            return "incorrect login details", 401
    else:
        return "User does not exist", 400


@app.route("/logout", methods=['PUT'])
def logout():
    # get access token from header and delete from db
    token = request.headers.get('Authorization')
    print(token, file=sys.stderr)
    token_db = AccessTokens.query.get(token)
    db.session.delete(token_db)
    db.session.commit()
    return "User logged out", 200

@app.route("/register", methods=['POST'])
def register():
    json_user = request.get_json()
    user_id = json_user['userId']
    password = json_user['password']

    # Check if user already registered
    user = Users.query.get(user_id)
    if user:
        return "User account already exists", 400

    # Prepend randomly generated salt to password and hash using argon2
    salt = bcrypt.gensalt()
    hashed_pword = flask_argon2.generate_password_hash(salt.decode("utf-8") + password)

    user_db = Users(user_id=user_id, password=hashed_pword, salt=salt)
    db.session.add(user_db)
    db.session.commit()

    # Create access token and store in db
    token = secrets.token_hex(16)
    token_db = AccessTokens(token=token, expiry=(datetime.now() + timedelta(days=2)))
    db.session.add(token_db)
    db.session.commit()

    json_token = json.dumps({'token': token})
    return json_token, 200

@app.route("/authenticate", methods=['PUT'])
def authenticate():
    # remove Bearer from start of token
    json_token= request.get_json()
    token = json_token['token']

    token = AccessTokens.query.get(token)
    if token:
        if token.expiry >= datetime.now():
            return "valid token", 200
        else:
            return "token expired", 401
    else:
        return "invalid token", 401

def main():
    db.drop_all()
    db.create_all()
    db.session.commit()

    app.run(host='0.0.0.0', port=80, debug=True)

if __name__ == "__main__":
    main()