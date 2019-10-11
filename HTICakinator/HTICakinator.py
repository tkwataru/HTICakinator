
# -*- coding: utf-8 -*-
# #!/usr/bin/env python3
import math
import json
import collections as cl
import argparse
import numpy as np
import heapq
import socket

THRESHOLD_ANS = 0.95 # 確率しきい値
MAX_QUESTIONS = 10 # 最大質問数
NUM_CHOICE = 1 # ランダム上位質問候補数

SERVER_IP = '127.0.0.1' # サーバーIPアドレス
SERVER_PORT = 50007 # サーバー接続ポート

class HTICakinator:
    def __init__(self, database_path):
        self.database = cl.OrderedDict()    # 辞書型の順序固定

        #json形式で質問データベースを書き込み
        #fw = open('database.json', 'w')
        #json.dump(self.database, fw, indent=4)
        #print(self.database)

        #json形式の質問データベースを読み込み
        fr = open(database_path, 'r', encoding="utf-8_sig")
        self.database = json.load(fr)
        #print(self.database)

        self.p = {};
        #init p
        for key in self.database.keys():
            self.p[key] = 1.0 / len(self.database.keys())
        
        self.q_list = []#[102123, 24511, 53355]]
        self.a_list = []
        self.threshold_ans = THRESHOLD_ANS
        self.max_questions = MAX_QUESTIONS

        #init diseases
        self.diseases = self.database.keys()

        #init candidate
        self.q_candidates = []
        for key in self.database.keys():
            qs = self.database[key]
            for q in qs.keys():
                self.q_candidates.append(q)
        
        self.q_candidates = list(set(self.q_candidates))

    def isLastQuestion(self):
        (disease, est) = self.getBestEstimate()
        if(est > self.threshold_ans):   # 確率がしきい値以上
            return True
        elif(len(self.q_list) >= self.max_questions):   # 最大質問数以上
            return True
        else:
            return False

    def calculateE(self, ps):
        entropy = 0
        for disease in self.diseases:
            entropy += - ps[disease] * math.log2(ps[disease])
        return entropy


    def calculateGainE(self, current_entropy, q):

        #first calc if a = 0
        ## calc weight for a = 0
        w_0 = 0
        ### p(disease) * p(ans = 0 | disease)
        for disease in self.diseases:
            w_0 += self.p[disease] * (1.0 * self.database[disease][q][0]/(self.database[disease][q][0]+self.database[disease][q][1]))
        
        ### calc_p after know
        p_0 = self.updateP(self.p, q, 0)
        e_0 = self.calculateE(p_0)

        #first calc if a = 1
        ## calc weight for a = 1
        w_1 = 1 - w_0

        p_1 = self.updateP(self.p, q, 1)
        e_1 = self.calculateE(p_1)

        # p(q_ans = 0) * E(q_ans=0) + p(q_ans = 1) * E(q_ans=1)
        return current_entropy - (w_0 * e_0 + w_1 * e_1)


    def showQ(self, q):
        print(" current p :  "+str(self.p))
        print (str(len(self.q_list)+1) + ":" + q + " (Y / y / Yes / yes)")
        # クライアントに質問送信
        self.conn.sendall((str(len(self.q_list)+1) + ":" + q + " (Y / y / Yes / yes)").encode('utf-8'))

    def isNeedContinueQ(self):
        if(self.isLastQuestion()):
            return False
        return True
    
    def decideQ(self):
    #search best question
        #max_e = float("-inf")
        #max_e_q = ""
        e_q_list = []

        cur_entropy = self.calculateE(self.p)

        for q_candidate in self.q_candidates:
            # 既出質問は飛ばす
            if q_candidate in self.q_list:
                continue

            e = self.calculateGainE(cur_entropy, q_candidate)
            e_q_list.append((e, q_candidate))

            # 最大エントロピーの質問を選択
            #if max_e < e:
            #    max_e = e
            #    max_e_q = q_candidate

        max_nth_e_q = np.array(heapq.nlargest(NUM_CHOICE, e_q_list))	# エントロピー上位n個の質問抽出
        print(max_nth_e_q)
        nth_p = max_nth_e_q[:,0].astype(np.float32) / np.sum(max_nth_e_q[:,0].astype(np.float32))
        return np.random.choice(max_nth_e_q[:,1], p = nth_p)	# エントロピーを選択確率として質問をランダム選択

        # return max_e_q

    def updateP(self, p, q, a):
        new_p = {}

        base_p = 0
        for disease in self.diseases:
            base_p += (self.database[disease][q][a]*1.0/(self.database[disease][q][0] + self.database[disease][q][1])) * p[disease]

        for disease in self.diseases:
            # p(c | qs, as, q, a) = p(a | c, q) | p(c | qs, as)
            new_p[disease] = 1.0 / base_p *(self.database[disease][q][a]*1.0/(self.database[disease][q][0] + self.database[disease][q][1])) * p[disease]

        return new_p
        
    def updateDatabase(self):
        (disease, est) = self.getBestEstimate()
        for q, a in zip(self.q_list, self.a_list):
            self.database[disease][q][a] += 1

    def getBestEstimate(self):
        maxEstimate = 0
        maxEstimateDisease = ""
        for disease in self.diseases:
            if maxEstimate < self.p[disease]:
                maxEstimate = self.p[disease]
                maxEstimateDisease = disease

        return (maxEstimateDisease, maxEstimate)

    def showAndAskAnswer(self):
        (disease, est) = self.getBestEstimate()
        print( disease + " : " + str(est) + " (Y / y / Yes / yes)")
        # クライアントに質問送信
        self.conn.sendall((disease + " : " + str(est) + " (Y / y / Yes / yes)").encode('utf-8'))

        last_ans = self.answer()
        return last_ans

    def answer(self):
        # input_text = input()
        # クライアントから回答受信待ち
        input_text = self.conn.recv(1024).decode('utf-8')
        if input_text == "Y" or input_text == "y" or input_text == "Yes" or  input_text == "yes":
            return 0
        else:
            return 1

    def socketConnect(self):
        # AF = IPv4 という意味
        # TCP/IP の場合は、SOCK_STREAM を使う
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # IPアドレスとポートを指定
            s.bind((SERVER_IP, SERVER_PORT))
            # 1 接続
            s.listen(1)
            # connection するまで待つ
            print("Waiting for connection...")
            self.conn, self.addr = s.accept()
            print("Connected:" + str(self.addr))

    def main(self):
        self.socketConnect()

        while(self.isNeedContinueQ()):
            q = self.decideQ()
            self.showQ(q)
            self.q_list.append(q)

            a = self.answer()
            self.a_list.append(a)
            self.p = self.updateP(self.p, q, a)

        print(" result p :  "+str(self.p))
        result = self.showAndAskAnswer()
        # クライアントに終了通知
        self.conn.sendall(b'END')
        #if result == True:
        #    self.updateDatabase()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='HTIC akinator')
    parser.add_argument('database_path', help='Path to database.json')
    args = parser.parse_args()
   
    hticakinator = HTICakinator(args.database_path)
    hticakinator.main()
    