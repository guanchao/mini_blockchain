# coding:utf-8

import json


class Block(object):
    def __init__(
            self,
            index,
            previous_hash,
            timestamp,
            nonce,
            current_hash,
            difficulty):
        """
        区块结构
        :param index: <int> 区块索引
        :param previous_hash: <str> 前一区块地址
        :param timestamp: <str> 时间戳
        :param nonce: <str> 当前区块POW共识过程的随机数
        :param current_hash: <str> 当前区块的目标哈希值
        :param difficulty: <int> 难度系数
        """
        # header
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.nonce = nonce
        self.current_hash = current_hash
        self.difficulty = difficulty
        self.merkleroot = None

        # body
        self.transactions = None  # <Transaction>对象数组

    def get_transactions(self):
        return self.transactions

    def json_output(self):
        output = {
            'index': self.index,
            'previous_hash': self.previous_hash,
            'timestamp': self.timestamp,
            'nonce': self.nonce,
            'current_hash': self.current_hash,
            'difficulty': self.difficulty,
            'merkleroot': self.merkleroot,
            'transactions': [tx.json_output() for tx in self.transactions]
        }
        return output

    def __str__(self):
        return json.dumps(
            self.json_output(),
            default=lambda obj: obj.__dict__,
            sort_keys=True,
            indent=4)
