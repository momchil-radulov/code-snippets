#!/usr/bin/python3
import hug, dataset
# gunicorn3 hug1:__hug_wsgi__ # how to start
# ssh -L 8000:localhost:8000 ubuntu@host # how to connect and test from external computer
# http://localhost:8000/ # how to test with browser
db = dataset.connect('sqlite:////root/git/db/users.db') # path to sqlite3 database file

@hug.get()
def roles():
    '''Says roles'''
    return db['role']

@hug.get('/role', examples="id=123")
def role(id:hug.types.number):
    '''Says role'''
    return db['role'].find(role_id=id)
