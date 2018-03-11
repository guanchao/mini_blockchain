# coding:utf-8

class Block(object):
    def __init__(self, index, previous_hash, timestamp, nonce, current_hash, difficulty):
        """
        区块结构
        :param index: <int> 区块索引
        :param previous_hash: <str> 前一区块地址
        :param timestamp: <str> 时间戳
        :param nonce: <str> 当前区块POW共识过程的解随机数
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
        self.transactions = None

    def get_json_obj(self):
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "difficulty": self.difficulty,
            "current_hash": self.current_hash,
            "transactions": self.transactions,
            "merkleroot": self.merkleroot
        }
