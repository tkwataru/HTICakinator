from flask import Flask, render_template, request, session, redirect, jsonify
import sqlite3
import pickle
from uuid import uuid4
from datetime import datetime, timedelta

from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import argparse
import socket
import threading

from HTICakinator2 import HTICakinator

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = 'change me!!'

_akinator_from_user = {}
_AKINATOR_LIFESPAN = timedelta(hours=1)


def delete_not_used_akinators():
    for user, akinator in list(_akinator_from_user.items()):
        if akinator.created_at + _AKINATOR_LIFESPAN < datetime.now():
            del _akinator_from_user[user]


def require_akinator(create=False):
    user = session['user'] = session.get('user', uuid4())
    if create and user not in _akinator_from_user:
        _akinator_from_user[user] = HTICakinator('database_dummy1011.json')
        _akinator_from_user[user].created_at = datetime.now()
        
    delete_not_used_akinators()
    
    return _akinator_from_user.get(user)


def delete_akinator():
    if 'user' in session and session['user'] in _akinator_from_user:
        del _akinator_from_user[session['user']]
    

@app.route('/', methods=['GET'])
def question():
    akinator = require_akinator(create=True)
    
    if akinator.finished():
        (disease, est) = akinator.getBestEstimate()
        return render_template('index2.html',
                               title='動悸チェッカーサンプル',
                               message='チェックが完了しました',
                               question='{}: {:.2%}'.format(disease, est))
    else:
        return render_template('index2.html',
                               title='動悸チェッカーサンプル',
                               message='あなたの動悸症状に関する質問に答えてください',
                               question=akinator.question())


@app.route('/answer/<yes_or_no>', methods=['GET'])
def answer(yes_or_no):
    akinator = require_akinator(create=False)
    if akinator is not None and not akinator.finished():
        akinator.answer(yes_or_no)
    return redirect('/')
    

@app.route('/reset', methods=['GET'])
def reset():
    delete_akinator()
    return redirect('/')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='HTIC akinator client dummy UI')
    parser.add_argument('--ip', default='127.0.0.1', help='Server IP address')
    parser.add_argument('--port', default=50007, type=int, help='Server connection port')
    args = parser.parse_args()

    app.debug = True
    app.run(host='localhost')
