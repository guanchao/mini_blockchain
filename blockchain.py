# coding:utf-8
import hashlib
from time import time
from uuid import uuid4

from Block import Block

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


def caculate_hash(index, previous_hash, timestamp, data, proof):
    value = str(index) + str(previous_hash) + str(timestamp) + str(data) + str(proof)
    sha = hashlib.sha256(value.encode('utf-8'))
    return str(sha.hexdigest())


def caculate_block_hash(block):
    return caculate_hash(block.index, block.previous_hash, block.timestamp, block.data, block.proof)


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

            if new_block_attempt.current_hash[0:self.difficulty] == '0' * self.difficulty:
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
            if self.__is_valid_new_block(chain[i], temp_chain[i - 1]):
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
