# coding:utf-8
import json


class Block(object):
    def __init__(self, index, previous_hash, timestamp, data, nonce, current_hash):
        """
        区块结构
        :param previous_hash: <str> 前一区块地址
        :param hash: <str> 当前区块的目标哈希值
        :param version: <int> 当前版本号
        :param nonce: <str> 当前区块POW共识过程的解随机数
        :param merkle_root: <object> 保存交易当前区块交易数据树结构
        """
        # header
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data
        self.nonce = nonce
        self.current_hash = current_hash
        self.merkletrees = None

        # body
        self.transactions = None

    def get_json_obj(self):
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "data": self.data,
            "nonce": self.nonce,
            "current_hash": self.current_hash,
            "merkletrees": json.dumps(self.merkletrees.get_transaction_tree()),
            "merkleroot" : self.merkletrees.get_root_leaf()
        }

