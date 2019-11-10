from flask import Flask, render_template, request, session, redirect, jsonify
import sqlite3
import pickle
from uuid import uuid4

from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import HTICakinator
import argparse
import socket
import threading

from HTICakinator2 import HTICakinator

MESSAGE = ''

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = 'change-me'

akinator_from_user = {}

@app.route('/', methods=['GET'])
def index():
    user = session['user'] = session.get('user', uuid4())
    if user not in akinator_from_user:
        akinator_from_user[user] = HTICakinator('database_dummy1011.json')
        akinator_from_user[user].q = None
    akinator = akinator_from_user[user]

    if akinator.isNeedContinueQ():
        if akinator.q is None:
            akinator.q = akinator.decideQ()
            akinator.q_list.append(akinator.q)

        return render_template('index2.html',
                               title='動悸チェッカーサンプル',
                               message='あなたの動悸症状に関する質問に答えてください ({})'.format(akinator.a_list),
                               question=akinator.q)
    else:
        (disease, est) = akinator.getBestEstimate()
        return render_template('index2.html',
                               title='動悸チェッカーサンプル',
                               message='あなたの動悸症状に関する質問に答えてください ({})'.format(akinator.a_list),
                               question='{}: {}'.format(disease, est))


@app.route('/answer/<yes_or_no>', methods=['GET'])
def answer(yes_or_no):
    if 'user' not in session or session['user'] not in akinator_from_user:
        return redirect('/')
    
    akinator = akinator_from_user[session['user']]
    
    if akinator.isNeedContinueQ():
        a = 0 if yes_or_no == 'yes' else 1
        akinator.a_list.append(a)
        akinator.p = akinator.updateP(akinator.p, akinator.q, a)
        akinator.q = None
    
    return redirect('/')
    

@app.route('/reset', methods=['GET'])
def reset():
    if 'user' not in session or session['user'] not in akinator_from_user:
        return redirect('/')
    del akinator_from_user[session['user']]
    return redirect('/')

def socketConnect():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # サーバを指定
        s.connect(('127.0.0.1', 50007))
        # s.connect((args.ip, args.port))

        while True:
            # ネットワークのバッファサイズは1024。サーバからの質問文字列を取得する
            message = s.recv(1024).decode('utf-8')
            if message == "END":
                break
            # 質問表示
            print(message)

            # 回答入力待ち
            input_text = input()

            # サーバに回答を送る
            s.sendall(input_text.encode('utf-8'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='HTIC akinator client dummy UI')
    parser.add_argument('--ip', default='127.0.0.1', help='Server IP address')
    parser.add_argument('--port', default=50007, type=int, help='Server connection port')
    args = parser.parse_args()

    # thread_1 = threading.Thread(target=socketConnect)
    # thread_1.start()

    app.debug = True
    app.run(host='localhost')
