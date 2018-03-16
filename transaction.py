# coding:utf-8

import hashlib
import json

import util
from walet import get_address


class Transaction(object):
    def __init__(self, txins, txouts, timestamp):
        """

        :param txid: <str> 交易id
        :param txin: <TxInput>数组
        :param txout: <TxOuput>数组
        """
        self.txins = txins
        self.txouts = txouts
        self.timestamp = timestamp
        self.txid = self.get_txid()

    def get_txid(self):
        value = str(self.timestamp) + ",".join(str(txin) for txin in self.txins) + ",".join(
            str(txout) for txout in self.txouts)
        sha = hashlib.sha256(value.encode('utf-8'))
        return str(sha.hexdigest())

    def get_hash(self):
        sha = hashlib.sha256(self.__str__())
        return sha.hexdigest()

    def is_coinbase(self):
        """
        coinbase不存在输入，txins为None
        :return:
        """
        return self.txins[0].prev_txid == None

    def json_output(self):
        output = {
            'txid': self.txid,
            'timestamp': self.timestamp,
            'txins': [txin.json_output() for txin in self.txins],
            'txouts': [txout.json_output() for txout in self.txouts]
        }
        return output

    def __str__(self):
        return json.dumps(self.json_output(), default=lambda obj: obj.__dict__, sort_keys=True, indent=4)


class TxOutput(object):
    """
    货币存储在TxOutput中，一个用户钱包的余额相当于某个地址下未使用过的TxOutput中value之和
    """

    def __init__(self, value, pubkey_hash):
        """

        :param value: 一定量的比特币
        :param pubkey_hash: 锁定脚本，要花这笔钱，必须要解锁该脚本（相当于问题，回答该问题就可以花这笔钱）。
                            目前将会存储一个任意的字符串，用做用户定义的钱包地址
        """
        self.value = value
        self.pubkey_hash = pubkey_hash

    def can_be_unlocked_with(self, unlocking_data):
        return self.pubkey_hash == unlocking_data

    def lock(self, address):
        """
        这里简化一下，钱包的地址就是公钥的哈希
        :param address:
        :return:
        """
        self.pubkey_hash = address

    def is_locked_with_key(self, pubkey_hash):
        return self.pubkey_hash == pubkey_hash

    def __str__(self):
        return json.dumps(self.json_output(), default=lambda obj: obj.__dict__, sort_keys=True, indent=4)

    def json_output(self):
        output = {
            'value': self.value,
            'pubkey_hash': self.pubkey_hash
        }
        return output


class TxInput(object):
    """
    一个输入引用之前的一个输出
    """

    def __init__(self, prev_txid, out_idx, signature, pubkey):
        """

        :param prev_txid: 指向之前的交易id
        :param out_idx: 存储上一笔交易中所有输出的索引（一个交易包含多个输出，需指明是哪一个）
        :param script_sig: script_sig是一个脚本，提供了可解锁输出结构里面ScriptPubKey字段的数据（相当于答案，对上一笔输出的回答）。如果ScriptSig提供的数据正确，
                            那么输出就会被解锁，然后被解锁的值就可以被用于产生新的输出；如果数据不正确，输出就无法被引用在输入中
        """
        self.prev_txid = prev_txid
        self.prev_tx_out_idx = out_idx
        self.signature = signature
        self.pubkey = pubkey

    def can_unlock_txoutput_with(self, unlocking_data):
        return get_address(self.pubkey) == unlocking_data

    #
    # def usekey(self, pubkey_hash):
    #     locking_hash = get_address(self.pubkey)
    #     return locking_hash == pubkey_hash


    def json_output(self):
        output = {
            'prev_txid': self.prev_txid,
            'prev_tx_out_idx': self.prev_tx_out_idx,
            'signature': util.get_hash(self.signature) if self.signature != None else "",
        }
        return output

    def __str__(self):
        return json.dumps(self.json_output(), default=lambda obj: obj.__dict__, sort_keys=True, indent=4)
