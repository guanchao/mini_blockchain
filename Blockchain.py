# coding:utf-8
import hashlib
from time import time
from uuid import uuid4

from Block import Block
from MerkleTrees import MerkleTrees
from transaction import *
from util import *

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


class Blockchain(object):
    def __init__(self):
        self.difficulty = 4
        self.chain = []
        self.current_transactions = []
        # Generate a globally unique address for this node
        self.node_id = str(uuid4()).replace('-', '')
        # 创世区块
        self.chain.append(self.get_genius_block())

    def get_genius_block(self):
        # coinbase_tx = self.new_coinbase_tx(self.node_id)
        txin = TxInput(None, -1, "Genius block!")
        txoutput = TxOutput(10, self.node_id)
        coinbase_tx = Transaction([txin], [txoutput])
        transactions = [coinbase_tx]

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

    def new_coinbase_tx(self, to_addr):
        """
        创世块，区块的第一笔交易，用于奖励矿工
        :param to_addr: 接收地址
        :return: <Transaction>对象
        """
        txin = TxInput(None, -1, "Reward to " + to_addr)
        txoutput = TxOutput(10, to_addr)
        tx = Transaction([txin], [txoutput])
        return tx

    def generate_block(self, merkleroot, next_timestamp, next_nonce):
        previous_block = self.get_last_block()
        next_index = previous_block.index + 1
        previous_hash = previous_block.current_hash

        next_block = Block(
            index=next_index,
            previous_hash=previous_hash,
            timestamp=next_timestamp,
            nonce=next_nonce,
            current_hash=calculate_hash(next_index, previous_hash, next_timestamp, merkleroot, next_nonce,
                                        self.difficulty),
            difficulty=self.difficulty
        )
        next_block.merkleroot = merkleroot

        return next_block

    def get_balance(self, address):
        """
        获取address地址的余额
        :param address:
        :return:
        """
        balance, _ = self.find_spendalbe_outputs(address)
        return balance

    def new_utxo_transaction(self, from_addr, to_addr, amount):
        """
        from_addr向to_addr发送amount量的货币，步骤：
        Step1：首先获取from_addr下未使用过的TxOutput输出
        Step2：获取上一步TxOutput列表中value之和sum，并与amount相比
        Step3：如果sum<amount，则标识from_addr余额不够，无法交易；如果sum>=amount，则from_addr足够余额用于交易，多出的部分用于找零
        Step4：构造Transaction对象，并传入此次交易的输入和输出
        Step5：TODO 广播
        :param from_addr:
        :param to_addr:
        :param amount:
        :return:
        """
        inputs = list()
        outputs = list()
        balance, unspent_txout_list = self.find_spendalbe_outputs(from_addr)
        if balance < amount:
            return -1

        # 构造Tx的输入
        for txid, out_idx, txout in unspent_txout_list:
            txin = TxInput(txid, out_idx, from_addr)
            inputs.append(txin)

        # 构造Tx的输出
        txout = TxOutput(amount, to_addr)
        outputs.append(txout)
        if balance > amount:
            # 找零
            # TODO 交易费
            outputs.append(TxOutput(balance-amount, from_addr))

        tx = Transaction(inputs, outputs)
        self.current_transactions.append(tx)
        return self.chain[-1].index + 1

    def find_spendalbe_outputs(self, from_addr):
        """
        获取from_addr可以用于交易的TxOutput（未使用过的），
        :param from_addr:
        :return:
        """
        unspent_txout_list = list()
        spent_txout_list = dict()
        balance = 0

        # Step1:获取from_addr下可以未使用过的TxOutput
        for i in range(len(self.chain)):
            block = self.chain[len(self.chain) - 1 - i]
            # 1.获取区块下的所有的交易
            transactions = block.get_transactions()
            for tx in transactions:
                txid = tx.txid  # 当前交易的id

                # 2.遍历某个交易下所有的TxInput
                if not tx.is_coinbase():
                    # 记录当前tx下被from_addr被使用过的上一次交易的输出，即记录txid和out_idx
                    for txin in tx.txins:
                        if txin.can_unlock_txoutput_with(from_addr):
                            spent_txid = txin.prev_txid
                            spent_tx_out_idx = txin.prev_tx_out_idx
                            if not spent_txout_list.has_key(spent_txid):
                                spent_txout_list[spent_txid] = list()
                            spent_txout_list[spent_txid].append(spent_tx_out_idx)

                # 3.遍历某个交易下所有的未使用过的TxOutput
                if not spent_txout_list.has_key(txid):
                    for out_idx in range(len(tx.txouts)):
                        txout = tx.txouts[out_idx]

                        if txout.can_be_unlocked_with(from_addr):
                            unspent_txout_list.append((txid, out_idx, txout))

        # Step2：计算这些未使用过的TxOutput货币之和
        for txid, out_idx, txout in unspent_txout_list:
            balance += txout.value

        return balance, unspent_txout_list


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
                new_block_attempt = self.generate_block(merkleroot, timestamp, nonce)
                end_timestamp = time()
                cos_timestamp = end_timestamp - timestamp
                print('New block found with nonce ' + str(nonce) + ' in ' + str(round(cos_timestamp, 2)) + ' seconds.')

                # 给工作量证明的节点提供奖励
                # 发送者为"0" 表明新挖出的币
                coinbase_tx = self.new_coinbase_tx(self.node_id)
                self.current_transactions.append(coinbase_tx)

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
        if not self.is_same_block(chain[0], self.get_genius_block()):
            print('Genesis Block Incorrecet')
            return False

        temp_chain = [chain[0]]
        for i in range(1, len(chain)):
            if self.__is_valid_new_block(chain[i], temp_chain[i - 1]):
                temp_chain.append(chain[i])
            else:
                return False
        return True

    def is_same_block(self, block1, block2):
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
        new_block_hash = calculate_block_hash(new_block)
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


