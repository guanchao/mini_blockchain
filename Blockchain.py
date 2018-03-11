# coding:utf-8
import hashlib
from time import time
from uuid import uuid4

from Block import Block
from MerkleTrees import MerkleTrees
from util import *

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


class Blockchain(object):
    def __init__(self):
        self.difficulty = 5
        self.chain = []
        self.current_transactions = []
        # Generate a globally unique address for this node
        self.node_identifier = str(uuid4()).replace('-', '')
        # 创世区块
        self.chain.append(self.get_genius_block())

    def get_genius_block(self):
        transactions = [{
            'sender': '0000000000000000000000000000000000000000000000000000000000000000',
            'receiver': self.node_identifier,
            'amount': 10
        }]
        merkletrees = MerkleTrees(transactions)
        merkleroot = merkletrees.get_root_leaf()
        nonce = 0

        genish_block_hash = calculate_hash(index=0,
                                          previous_hash='0000000000000000000000000000000000000000000000000000000000000000',
                                          timestamp='1496518102.896031',
                                          merkleroot=merkleroot,
                                          nonce=nonce,
                                          difficulty=self.difficulty)
        while genish_block_hash[0:self.difficulty] != '0' * self.difficulty:
            genish_block_hash = calculate_hash(index=0,
                                              previous_hash='0000000000000000000000000000000000000000000000000000000000000000',
                                              timestamp='1496518102.896031',
                                              merkleroot=merkleroot,
                                              nonce=nonce,
                                              difficulty=self.difficulty)
            nonce += 1
        genius_block = Block(index=0,
                             previous_hash='0000000000000000000000000000000000000000000000000000000000000000',
                             timestamp='1496518102.896031',
                             nonce=nonce,
                             current_hash=genish_block_hash,
                             difficulty=self.difficulty)
        genius_block.merkleroot = merkleroot
        genius_block.transactions = transactions

        return genius_block

    def __generate_block(self, merkleroot, next_timestamp, next_nonce):
        previous_block = self.get_last_block()
        next_index = previous_block.index + 1
        previous_hash = previous_block.current_hash

        next_block = Block(
            index=next_index,
            previous_hash=previous_hash,
            timestamp=next_timestamp,
            nonce=next_nonce,
            current_hash=calculate_hash(next_index, previous_hash, next_timestamp, merkleroot, next_nonce, self.difficulty),
            difficulty=self.difficulty
        )
        next_block.merkleroot = merkleroot

        return next_block

    def new_transaction(self, sender, receiver, amount):
        self.current_transactions.append({
            'sender': sender,
            'receiver': receiver,
            'amount': amount
        })
        return self.chain[-1].index + 1

    def do_mine(self):
        nonce = 0
        timestamp = time()
        print('Minning a block...')
        new_block_found = False
        new_block_attempt = None

        merkletrees = MerkleTrees(self.current_transactions)
        merkleroot = merkletrees.get_root_leaf()
        while not new_block_found:
            # print "["+str(nonce)+"]", new_block_attempt.current_hash
            previous_block = self.get_last_block()
            next_index = previous_block.index + 1
            previous_hash = previous_block.current_hash
            cal_hash = calculate_hash(next_index, previous_hash, timestamp, merkleroot, nonce, self.difficulty)

            if cal_hash[0:self.difficulty] == '0' * self.difficulty:
                new_block_attempt = self.__generate_block(merkleroot, timestamp, nonce)
                end_timestamp = time()
                cos_timestamp = end_timestamp - timestamp
                print('New block found with nonce ' + str(nonce) + ' in ' + str(round(cos_timestamp, 2)) + ' seconds.')

                # 给工作量证明的节点提供奖励
                # 发送者为"0" 表明新挖出的币
                self.new_transaction(
                    sender='0',
                    receiver=self.node_identifier,
                    amount=10
                )

                # 添加到区块链中
                # 将所有交易保存成Merkle树
                new_block_attempt.transactions = self.current_transactions
                new_block_attempt.merkleroot = merkleroot
                self.chain.append(new_block_attempt)
                self.current_transactions = []

                new_block_found = True
            else:
                nonce += 1

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
        elif block1.merkleroot != block2.merkleroot:
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
