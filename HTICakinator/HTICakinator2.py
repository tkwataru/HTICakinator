
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
MAX_QUESTIONS = 10 # 最大出題質問数
NUM_CHOICE = 1 # ランダム上位質問候補数


class HTICakinator:
    def __init__(self, database_path):
        self._database = cl.OrderedDict()    # 辞書型の順序固定

        #json形式の質問データベースを読み込み
        with open(database_path, 'r', encoding="utf-8_sig") as fr:
            self._database = json.load(fr)
            self._assert_valid_database(self._database)
        
        self._p = {}
        #init p
        for key in self._database.keys():
            self._p[key] = 1.0 / len(self._database.keys())
        
        self._q_list = []
        self._a_list = []
        self._threshold_ans = THRESHOLD_ANS
        self._max_questions = MAX_QUESTIONS

        #init diseases
        self._diseases = self._database.keys()

        #init candidate
        self._q_candidates = []
        for key in self._database.keys():
            qs = self._database[key]
            for q in qs.keys():
                self._q_candidates.append(q)
        
        self._q_candidates = list(set(self._q_candidates))
        
        # init first question
        self._q_list.append(self._decideQ())
        
    def _assert_valid_database(self, database):
        all_questions = {q for qs in database.values() for q in qs}
        for q in all_questions:
            for questions in database.values():
                assert q in questions

    def _calculateE(self, ps):
        entropy = 0
        for disease in self._diseases:
            entropy += - ps[disease] * math.log2(ps[disease])
        return entropy


    def _calculateGainE(self, current_entropy, q):

        #first calc if a = 0
        ## calc weight for a = 0
        w_0 = 0
        ### p(disease) * p(ans = 0 | disease)
        for disease in self._diseases:
            w_0 += self._p[disease] * (1.0 * self._database[disease][q][0]/(self._database[disease][q][0]+self._database[disease][q][1]))
        
        ### calc_p after know
        p_0 = self._newP(self._p, q, 0)
        e_0 = self._calculateE(p_0)

        #first calc if a = 1
        ## calc weight for a = 1
        w_1 = 1 - w_0

        p_1 = self._newP(self._p, q, 1)
        e_1 = self._calculateE(p_1)

        # p(q_ans = 0) * E(q_ans=0) + p(q_ans = 1) * E(q_ans=1)
        return current_entropy - (w_0 * e_0 + w_1 * e_1)

    def _decideQ(self):
        #search best question
        e_q_list = []

        cur_entropy = self._calculateE(self._p)

        for q_candidate in self._q_candidates:
            # 既出質問は飛ばす
            if q_candidate in self._q_list:
                continue

            e = self._calculateGainE(cur_entropy, q_candidate)
            e_q_list.append((e, q_candidate))

        max_nth_e_q = np.array(heapq.nlargest(NUM_CHOICE, e_q_list))	# エントロピー上位n個の質問抽出
        print(max_nth_e_q)
        nth_p = max_nth_e_q[:,0].astype(np.float32) / np.sum(max_nth_e_q[:,0].astype(np.float32))
        return np.random.choice(max_nth_e_q[:,1], p = nth_p)	# エントロピーを選択確率として質問をランダム選択

    def _newP(self, p, q, a):
        new_p = {}

        base_p = 0
        for disease in self._diseases:
            base_p += (self._database[disease][q][a]*1.0/(self._database[disease][q][0] + self._database[disease][q][1])) * p[disease]

        for disease in self._diseases:
            # p(c | qs, as, q, a) = p(a | c, q) | p(c | qs, as)
            new_p[disease] = 1.0 / base_p *(self._database[disease][q][a]*1.0/(self._database[disease][q][0] + self._database[disease][q][1])) * p[disease]

        return new_p
        
    def question(self):
        if self.finished():
            return None
        else:
            return self._q_list[-1]
    
    def answer(self, a):
        assert not self.finished(), 'already finished'
        
        a = {'yes': 0, 'no': 1}[a]
        self._p = self._newP(self._p, self._q_list[-1], a)
        self._a_list.append(a)
        self._q_list.append(self._decideQ())
    
    def finished(self):
        (disease, est) = self.getBestEstimate()
        if(est > self._threshold_ans):   # 確率がしきい値を超えている
            return True
        elif(len(self._q_list) > self._max_questions):   # 最大出題質問数を超えている
            return True
        else:
            return False
        
    def getBestEstimate(self):
        maxEstimate = 0
        maxEstimateDisease = ""
        for disease in self._diseases:
            if maxEstimate < self._p[disease]:
                maxEstimate = self._p[disease]
                maxEstimateDisease = disease

        return (maxEstimateDisease, maxEstimate)
    
    def estimate(self):
        return dict(self._p)