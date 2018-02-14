# coding:utf-8
import hashlib
import json
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
import requests


"""
简化的区块链

功能：
1.可以进行挖矿
2.可以进行交易
3.可以进行简单工作量证明
4.可以进行简单共识


TODO:
1.POW机制扩展
2.共识扩展
3.p2p网络发现

"""


def caculate_hash(index, previous_hash, timestamp, data, proof):
    value = str(index) + str(previous_hash) + str(timestamp) + str(data) + str(proof)
    sha = hashlib.sha256(value.encode('utf-8'))
    return str(sha.hexdigest())

def caculate_block_hash(block):
    return caculate_hash(block.index, block.previous_hash, block.timestamp, block.data, block.proof)


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


class Blockchain(object):

    def __init__(self):
        self.difficulty = 4
        self.chain = []
        self.current_transactions = []
        # Generate a globally unique address for this node
        self.node_identifier = str(uuid4()).replace('-', '')
        # 创世区块
        self.chain.append(self.get_genius_block())

    def get_genius_block(self):
        genish_block_hash = caculate_hash(0, '0', '1496518102.896031', 'This is genius block!', 0)
        return Block(0, '0', '1496518102.896031', 'This is genius block!', 0, genish_block_hash)

    def __generate_block(self, next_data, next_timestamp, next_proof):
        previous_block = self.get_last_block()
        next_index = previous_block.index + 1
        previous_hash = previous_block.current_hash

        next_block = Block(
            next_index,
            previous_hash,
            next_timestamp,
            next_data,
            next_proof,
            caculate_hash(next_index, previous_hash, next_timestamp, next_data, next_proof)
        )

        return next_block

    def new_transaction(self, sender, receiver, amount):
        self.current_transactions.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount
        })
        return self.chain[-1].index + 1

    def do_mine(self):
        proof = 0
        timestamp = time()
        print('Minning a block...')
        new_block_found = False
        new_block_attempt = None

        while not new_block_found:
            new_block_attempt = self.__generate_block("Mine block", timestamp, proof)
            # print "["+str(proof)+"]", new_block_attempt.current_hash

            if new_block_attempt.current_hash[0:self.difficulty] == '0'*self.difficulty:
                end_timestamp = time()
                cos_timestamp = end_timestamp - timestamp
                print('New block found with proof ' + str(proof) + ' in ' + str(round(cos_timestamp, 2)) + ' seconds.')

                # 给工作量证明的节点提供奖励
                # 发送者为"0" 表明新挖出的币
                self.new_transaction(
                    sender='0',
                    receiver=self.node_identifier,
                    amount=10
                )

                # 添加到区块链中
                new_block_attempt.transactions = self.current_transactions
                self.chain.append(new_block_attempt)
                self.current_transactions = []

                new_block_found = True
            else:
                proof += 1

        return new_block_attempt

    def get_last_block(self):
        return self.chain[-1]

    def is_valid_chain(self, chain):
        if not self.__is_same_block(chain[0], self.get_genius_block()):
            print('Genesis Block Incorrecet')
            return False

        temp_chain = [chain[0]]
        for i in range(1, len(chain)):
            if self.__is_valid_new_block(chain[i], temp_chain[i-1]):
                temp_chain.append(chain[i])
            else:
                return False
        return True

    def __is_same_block(self, block1, block2):
        if block1.index != block2.index:
            return False
        elif block1.previous_hash != block2.previous_hash:
            return False
        elif block1.timestamp != block2.timestamp:
            return False
        elif hashlib.sha256(block1.data).hexdigest() != hashlib.sha256(block2.data).hexdigest():
            return False
        elif block1.current_hash != block2.current_hash:
            return False
        return True

    def __is_valid_new_block(self, new_block, previous_block):
        """
        1.校验index是否相邻
        2.校验hash
        :param new_block:
        :param previous_block:
        :return:
        """
        new_block_hash = caculate_block_hash(new_block)
        if previous_block.index + 1 != new_block.index:
            print('Indices Do Not Match Up')
            return False
        elif previous_block.current_hash != new_block.previous_hash:
            print('Previous hash does not match')
            return False
        elif new_block_hash != new_block.current_hash:
            print('Hash is invalid')
            return False
        return True

    def get_full_chain(self):
        output_chain_list = []
        for i in range(len(self.chain)):
            output_chain_list.append(self.chain[i].get_json_obj())
        return output_chain_list



app = Flask(__name__)

blockchain = Blockchain()
@app.route('/mine', methods=['GET'])
def mine():
    block = blockchain.do_mine()

    response = {
        'message': 'New Block Forged',
        'index': block.index,
        'transactions': block.transactions,
        'proof': block.proof,
        'previous_hash': block.previous_hash
    }
    return jsonify(response), 200

@app.route('/chain', methods=['GET'])
def full_chain():

    response = {
        'chain': blockchain.get_full_chain(),
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender', 'receiver', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['sender'], values['receiver'], values['amount'])
    response = {'message': 'Transaction will be added to Block' + str(index)}
    return jsonify(response), 201

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    app.run(host='0.0.0.0', port=port)


