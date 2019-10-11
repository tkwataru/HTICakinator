# -*- coding: utf-8 -*-
# #!/usr/bin/env python3
import argparse
import socket


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='HTIC akinator client dummy UI')
    parser.add_argument('--ip', default='127.0.0.1', help='Server IP address')
    parser.add_argument('--port', default=50007, type=int, help='Server connection port')
    args = parser.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # サーバを指定
        # s.connect(('127.0.0.1', 50007))
        s.connect((args.ip, args.port))

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

   
