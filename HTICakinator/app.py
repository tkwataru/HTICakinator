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

Q_DATABASE = 'database_dummy1115.json'

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = 'change me!!'

_akinator_from_user = {}
_AKINATOR_TIMEOUT = timedelta(hours=1)


def delete_not_used_akinators():
    for user, akinator in list(_akinator_from_user.items()):
        if akinator.timeout < datetime.now():
            del _akinator_from_user[user]


def require_akinator(create=False, database=''):
    delete_not_used_akinators()
    
    user = session['user'] = session.get('user', uuid4())
    if create and user not in _akinator_from_user:
        _akinator_from_user[user] = HTICakinator(database)
    
    akinator = _akinator_from_user.get(user)
    if akinator is not None:
        akinator.timeout = datetime.now() + _AKINATOR_TIMEOUT
        
    return akinator


def delete_akinator():
    if 'user' in session and session['user'] in _akinator_from_user:
        del _akinator_from_user[session['user']]
    

@app.route('/', methods=['GET'])
def question():
    ### 質問データベース選択のための初期必須質問はここに書く ###

    akinator = require_akinator(create=True, database=Q_DATABASE)
    
    if akinator.finished():
        (disease, est) = akinator.getBestEstimate()
        return render_template('index2.html',
                               title='動悸チェッカーサンプル',
                               message='チェックが完了しました',
                               question='{}: {:.0%}'.format(disease, est))
    else:
        return render_template('index2.html',
                               title='動悸チェッカーサンプル',
                               message='あなたの動悸症状に関する質問に答えてください',
                               question=akinator.question(),
                               confidence=', '.join('{}: {:.0%}'.format(disease, conf) for disease, conf in akinator.estimate().items()))


@app.route('/answer/<yes_or_no_or_unknown>', methods=['GET'])
def answer(yes_or_no_or_unknown):
    akinator = require_akinator(create=False)
    if akinator is not None and not akinator.finished():
        akinator.answer(yes_or_no_or_unknown)
    return redirect('/')
    

@app.route('/reset', methods=['GET'])
def reset():
    delete_akinator()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True, host='localhost')
    # app.run(debug=False, host='0.0.0.0') # public IP
