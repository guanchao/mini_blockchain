# coding:utf-8

class Block(object):
    def __init__(self, index, previous_hash, timestamp, data, proof, current_hash):
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
        self.proof = proof
        self.current_hash = current_hash

        # body
        self.transactions = None

    def get_json_obj(self):
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "data": self.data,
            "proof": self.proof,
            "current_hash": self.current_hash,
            "transactions": self.transactions
        }
