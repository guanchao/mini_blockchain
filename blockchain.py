# coding:utf-8
from binascii import hexlify, Error
from time import time

import rsa

import db
import wallet
from Block import Block
from MerkleTrees import MerkleTrees
from transaction import *
from util import *

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


class Blockchain(object):
    def __init__(self, genisus_node=False):
        """

        :param genisus_node: 判断是否是创世节点，如果是则读取本地（genisus_public.pem和genisus_private.pem）密钥对，
                            创始区块的第一笔交易就是奖励给genisus_public.pem
        """
        self.difficulty = 4
        self.current_transactions = []
        self.wallet = wallet.Wallet(genisus_node)
        genius_block = self.get_genius_block()  # 创世区块
        db.write_to_db(self.wallet.address, genius_block)
        self.candidate_blocks = {}

    def get_genisus_pubkey(self):
        """
        获取创世节点的公钥。<rsa.key.PublicKey>对象
        :return:
        """
        with open('genisus_public.pem', 'r') as f:
            pubkey = rsa.PublicKey.load_pkcs1(f.read().encode())
        return pubkey

    def get_genius_block(self):
        """
        创建创始区块
        :return: 返回<Transaction>对象
        """
        txin = TxInput(None, -1, None, None)
        pubkey_hash = Script.sha160(str(self.get_genisus_pubkey()))
        txoutput = TxOutput(100, pubkey_hash)
        coinbase_tx = Transaction([txin], [txoutput], 1496518102)  # 创世区块的第一笔交易
        transactions = [coinbase_tx]

        merkletrees = MerkleTrees(transactions)
        merkleroot = merkletrees.get_root_leaf()
        nonce = 0

        genish_block_hash = calculate_hash(index=0,
                                           previous_hash='00000000000000000000000000000000000000000000000000000000000000',
                                           timestamp=1496518102,
                                           merkleroot=merkleroot,
                                           nonce=nonce,
                                           difficulty=self.difficulty)
        while genish_block_hash[0:self.difficulty] != '0' * self.difficulty:
            genish_block_hash = calculate_hash(index=0,
                                               previous_hash='00000000000000000000000000000000000000000000000000000000000000',
                                               timestamp=1496518102,
                                               merkleroot=merkleroot,
                                               nonce=nonce,
                                               difficulty=self.difficulty)
            nonce += 1
        genius_block = Block(index=0,
                             previous_hash='00000000000000000000000000000000000000000000000000000000000000',
                             timestamp=1496518102,
                             nonce=nonce,
                             current_hash=genish_block_hash,
                             difficulty=self.difficulty)
        genius_block.merkleroot = merkleroot
        genius_block.transactions = transactions

        return genius_block

    def new_coinbase_tx(self, address):
        """
        创世块，区块的第一笔交易，用于奖励矿工
        :param address: <str> 钱包接收地址
        :return: <Transaction>对象
        """
        txin = TxInput(None, -1, None, None)
        pubkey_hash = hexlify(Wallet.b58decode(address)).decode('utf8')
        txoutput = TxOutput(10, pubkey_hash)
        tx = Transaction([txin], [txoutput], int(time()))
        return tx

    def generate_block(self, merkleroot, next_timestamp, next_nonce):
        """
        创建区块
        :param merkleroot: <str> 默克尔树根节点
        :param next_timestamp:
        :param next_nonce:
        :return:
        """
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

    def trimmed_copy_tx(self, tx):
        """
        被修剪后的带待签名副本，该副本包含交易中的所有输入和输出，
        但是TxInput.signature和TxInput.pubkey被设置未None
        :param tx: <Transaction>对象，待修剪、拷贝的交易
        :return:
        """
        inputs = list()
        outputs = list()

        for txin in tx.txins:
            inputs.append(TxInput(txin.prev_txid, txin.prev_tx_out_idx, None, None))

        for txout in tx.txouts:
            outputs.append(TxOutput(txout.value, txout.pubkey_hash))

        return Transaction(inputs, outputs, tx.timestamp)

    def sign(self, tx, privkey, prev_txid_2_tx):
        """
        用私钥对交易tx签名
        :param tx: <Transaction>对象，待签名对象
        :param privkey: <rsa.key.PrivateKey>对象，私钥
        :param prev_txid_2_tx: <dict>，txid与tx的映射
        :return:
        """
        if tx.is_coinbase():
            return

        tx_copy = self.trimmed_copy_tx(tx)  # 每个输入的signature和pubkey设置为None

        signature_flag = dict()
        for in_idx in range(len(tx_copy.txins)):
            txin = tx_copy.txins[-1 - in_idx]
            prev_tx = prev_txid_2_tx[txin.prev_txid]

            txin.signature = None
            txin.pubkey = prev_tx.txouts[txin.prev_tx_out_idx].pubkey_hash
            data = tx_copy.get_hash()  # 待签名数据
            txin.pubkey = None

            signature = rsa.sign(data.encode(), privkey, 'SHA-256')
            signature_flag[in_idx] = signature

        for in_idx in range(len(tx_copy.txins)):
            if in_idx in signature_flag:
                tx.txins[in_idx].signature = signature_flag[in_idx]

    def sign_transaction(self, tx, privkey):
        """

        :param tx:  <Transaction>对象，待签名对象
        :param privkey: <rsa.key.PrivateKey>对象，私钥
        :return:
        """

        prev_txid_2_tx = dict()
        for txin in tx.txins:
            prev_txid_2_tx[txin.prev_txid] = self.find_transaction(txin.prev_txid)
        self.sign(tx, privkey, prev_txid_2_tx)

    def verify_transaction(self, tx):
        """
        验证一笔交易

        :param tx: <Transaction>对象
        :return:
        """

        prev_txid_2_tx = dict()
        for txin in tx.txins:
            prev_txid_2_tx[txin.prev_txid] = self.find_transaction(txin.prev_txid)

        return self.verify(tx, prev_txid_2_tx)

    def verify(self, tx, prev_txid_2_tx):
        """
        验证一笔交易
        rsa.verify(data.encode(), signature, pubkey)
        :param tx: <Transaction>对象
        :param prev_txid_2_tx: <dict>，txid与tx的映射
        :return:
        """
        if tx.is_coinbase():
            return True
        tx_copy = self.trimmed_copy_tx(tx)  # 每个输入的signature和pubkey设置未None
        for in_idx in range(len(tx_copy.txins)):
            # 校验每一个输入的有效性(即检查解锁脚本是否有效)
            txin = tx_copy.txins[-1 - in_idx]
            prev_tx = prev_txid_2_tx[txin.prev_txid]
            if not prev_tx:
                # 区块不存在
                return False
            txin.signature = None
            txin.pubkey = prev_tx.txouts[txin.prev_tx_out_idx].pubkey_hash
            data = tx_copy.get_hash()  # 待签名数据

            txin.pubkey = None

            scriptSig = [tx.txins[in_idx].signature, tx.txins[in_idx].pubkey]  # 解锁脚本
            scriptPubKey = prev_tx.txouts[txin.prev_tx_out_idx].get_scriptPubKey()  # 锁定脚本

            if not Script.check_tx_script(data, scriptSig, scriptPubKey):
                return False

        return True

    def find_transaction(self, txid):
        """
        通过交易id找到一笔Tx交易
        :param txid: <str>交易id
        :return:
        """
        # 在区块中寻找（已确认的交易）
        block_height = db.get_block_height(self.wallet.address)

        for index in range(block_height):
            block = db.get_block_data_by_index(self.wallet.address, index)
            # 1.获取区块下的所有的交易
            transactions = block.get_transactions()
            for tx in transactions:
                if tx.txid == txid:
                    return tx

        # 在交易池中寻找（未确认的交易）TODO待确认
        for k in range(len(self.current_transactions)):
            uncomfirmed_tx = self.current_transactions[-1 - k]
            if uncomfirmed_tx.txid == txid:
                return uncomfirmed_tx
        return None

    def get_balance(self, address):
        """
        获取address地址的余额
        :param address: <str> 钱包地址
        :return:
        """
        balance, _ = self.find_spendalbe_outputs(address)
        return balance

    def get_wallet_address(self):
        return self.wallet.address

    def new_utxo_transaction(self, from_addr, to_addr, amount):
        """
        from_addr向to_addr发送amount量的货币，步骤：
        Step1：首先从区块中获取from_addr下未使用过的TxOutput输出(未使用的UTXO)
        Step2：获取上一步TxOutput列表中value之和sum，并与amount相比
        Step3：如果sum<amount，则标识from_addr余额不够，无法交易；如果sum>=amount，则from_addr足够余额用于交易，多出的部分用于找零
        Step4：构造Transaction对象，并传入此次交易的输入和输出
        Step5：输入检查交易的有效性，输出设置锁定脚本
        Step6：广播

        :param from_addr: <str>,发送方钱包地址
        :param to_addr: <str>,接收方钱包地址
        :param amount: <int>,金额
        :return:
        """
        inputs = list()
        outputs = list()
        balance, unspent_txout_list = self.find_spendalbe_outputs(from_addr)
        if balance < amount:
            print 'not enough money!'
            return None

        # 构造Tx的输入
        for txid, out_idx, txout in unspent_txout_list:
            txin = TxInput(txid, out_idx, None, self.wallet.pubkey)
            inputs.append(txin)

        # 构造Tx的输出
        txout = TxOutput(amount, hexlify(Wallet.b58decode(to_addr)).decode('utf8'))
        outputs.append(txout)
        if balance > amount:
            # 找零
            outputs.append(TxOutput(balance - amount, Script.sha160(str(self.wallet.pubkey))))

        tx = Transaction(inputs, outputs, int(time()))
        self.sign_transaction(tx, self.wallet.privkey)  # 签名Tx

        self.current_transactions.append(tx)
        db.write_unconfirmed_tx_to_db(self.wallet.address, tx)
        return tx

    def get_balance_by_db(self, from_addr):
        """
        获取from_addr可以用于交易的TxOutput（未使用过的），读取交易池和区块链的本地副本，避免被加锁
        :param from_addr: <str>发送方钱包地址
        :return: <int>
        """
        unspent_txout_list = list()
        spent_txout_list = list()
        balance = 0
        # Step1：遍历交易池中已经发生过的交易（未打包进区块，未确认）
        # 备注：要从最新的交易开始遍历!!!!!
        current_transactions = db.get_all_unconfirmed_tx(self.wallet.address)
        current_transactions = sorted(current_transactions, key=lambda x: x.timestamp, reverse=False)
        for i in range(len(current_transactions)):
            unconfirmed_tx = current_transactions[len(current_transactions) - 1 - i]
            txid = unconfirmed_tx.txid

            # 遍历当前交易下所有的TxInput
            if not unconfirmed_tx.is_coinbase():
                # print 'txid:', txid
                # 记录当前tx下被from_addr被使用过的上一次交易的输出，即记录txid和out_idx
                for txin in unconfirmed_tx.txins:
                    if txin.can_unlock_txoutput_with(from_addr):
                        spent_txid = txin.prev_txid
                        spent_tx_out_idx = txin.prev_tx_out_idx
                        spent_txout_list.append((spent_txid, spent_tx_out_idx))

            # 遍历交易下所有的未使用过的TxOutput
            for out_idx in range(len(unconfirmed_tx.txouts)):
                txout = unconfirmed_tx.txouts[out_idx]
                if not (txid, out_idx) in spent_txout_list:
                    if txout.can_be_unlocked_with(from_addr):
                        unspent_txout_list.append((txid, out_idx, txout))
        # --------------------------------------------------

        # Step2:获取from_addr下可以未使用过的TxOutput（打包在区块，已确认）
        block_height = db.get_block_height(self.wallet.address)

        for i in range(block_height):
            block = db.get_block_data_by_index(self.wallet.address, block_height - 1 - i)
            # 1.获取区块下的所有的交易
            transactions = block.get_transactions()
            # 备注：要从最新的交易开始遍历!!!!!
            for k in range(len(transactions)):
                tx = transactions[len(transactions) - 1 - k]
                if not self.verify_transaction(tx):  # 校验交易是否有效
                    continue
                txid = tx.txid  # 当前交易的id

                # 2.遍历某个交易下所有的TxInput
                if not tx.is_coinbase():
                    # 记录当前tx下被from_addr被使用过的上一次交易的输出，即记录txid和out_idx
                    for txin in tx.txins:
                        if txin.can_unlock_txoutput_with(from_addr):
                            spent_txid = txin.prev_txid
                            spent_tx_out_idx = txin.prev_tx_out_idx
                            spent_txout_list.append((spent_txid, spent_tx_out_idx))

                # 3.遍历某个交易下所有的未使用过的TxOutput
                for out_idx in range(len(tx.txouts)):
                    txout = tx.txouts[out_idx]
                    if not (txid, out_idx) in spent_txout_list:
                        if txout.can_be_unlocked_with(from_addr):
                            unspent_txout_list.append((txid, out_idx, txout))

        # Step2：计算这些未使用过的TxOutput输出之和
        for txid, out_idx, txout in unspent_txout_list:
            balance += txout.value
        return balance

    def find_spendalbe_outputs(self, from_addr):
        """
        获取from_addr可以用于交易的TxOutput（未使用过的），
        :param from_addr: <str>发送方钱包地址
        :return:
        """
        unspent_txout_list = list()
        spent_txout_list = list()
        balance = 0
        # Step0：遍历交易池中已经发生过的交易（未打包进区块，未确认）
        # 备注：要从最新的交易开始遍历!!!!!
        for i in range(len(self.current_transactions)):
            unconfirmed_tx = self.current_transactions[len(self.current_transactions) - 1 - i]
            txid = unconfirmed_tx.txid

            # 遍历当前交易下所有的TxInput
            if not unconfirmed_tx.is_coinbase():
                # print 'txid:', txid
                # 记录当前tx下被from_addr被使用过的上一次交易的输出，即记录txid和out_idx
                for txin in unconfirmed_tx.txins:
                    if txin.can_unlock_txoutput_with(from_addr):
                        spent_txid = txin.prev_txid
                        spent_tx_out_idx = txin.prev_tx_out_idx
                        spent_txout_list.append((spent_txid, spent_tx_out_idx))

            # 遍历交易下所有的未使用过的TxOutput
            for out_idx in range(len(unconfirmed_tx.txouts)):
                txout = unconfirmed_tx.txouts[out_idx]
                if not (txid, out_idx) in spent_txout_list:
                    if txout.can_be_unlocked_with(from_addr):
                        unspent_txout_list.append((txid, out_idx, txout))
        # --------------------------------------------------

        # Step1:获取from_addr下可以未使用过的TxOutput（打包在区块，已确认）
        block_height = db.get_block_height(self.wallet.address)

        for i in range(block_height):
            block = db.get_block_data_by_index(self.wallet.address, block_height - 1 - i)
            # 1.获取区块下的所有的交易
            transactions = block.get_transactions()
            # 备注：要从最新的交易开始遍历!!!!!
            for k in range(len(transactions)):
                tx = transactions[len(transactions) - 1 - k]
                if not self.verify_transaction(tx):  # 校验交易是否有效
                    print '[Info] invalid tx', tx.txid, 'block index:', i
                    continue
                txid = tx.txid  # 当前交易的id

                # 2.遍历某个交易下所有的TxInput
                if not tx.is_coinbase():
                    # 记录当前tx下被from_addr被使用过的上一次交易的输出，即记录txid和out_idx
                    for txin in tx.txins:
                        if txin.can_unlock_txoutput_with(from_addr):
                            spent_txid = txin.prev_txid
                            spent_tx_out_idx = txin.prev_tx_out_idx
                            spent_txout_list.append((spent_txid, spent_tx_out_idx))

                # 3.遍历某个交易下所有的未使用过的TxOutput
                for out_idx in range(len(tx.txouts)):
                    txout = tx.txouts[out_idx]
                    if not (txid, out_idx) in spent_txout_list:
                        if txout.can_be_unlocked_with(from_addr):
                            unspent_txout_list.append((txid, out_idx, txout))

        # Step2：计算这些未使用过的TxOutput输出之和
        for txid, out_idx, txout in unspent_txout_list:
            balance += txout.value
        return balance, unspent_txout_list

    def do_mine(self):
        """
        进行挖矿，验证当前节点收集的交易，并将有效交易打包成区块

        :return:
        """

        nonce = 0
        timestamp = int(time())
        # print('Minning a block...')
        new_block_found = False
        new_block_attempt = None

        # 验证每一笔交易的有效性(备注：从最新的开始验证)
        for idx in range(len(self.current_transactions)):
            tx = self.current_transactions[-1 - idx]
            if not self.verify_transaction(tx):
                txid = tx.txid
                print "[Info] Invalid transaction, remove it, tx:"
                raise Error("[Error] do mine:Invalid transaction, remove it. Txid:" + txid)

        if len(self.current_transactions) < 5:
            # 至少要有5个以上的交易才可以开始进行挖矿
            raise Error("[Error] Not enough valid transactions!")

        # TODO
        # 给工作量证明的节点提供奖励
        # 发送者为"0" 表明新挖出的币
        # coinbase_tx = self.new_coinbase_tx(self.get_wallet_address())
        # valid_transactions.append(coinbase_tx)
        self.current_transactions = sorted(self.current_transactions, key=lambda x: x.timestamp,
                                           reverse=False)  # 时间由小到大排

        merkletrees = MerkleTrees(self.current_transactions)
        merkleroot = merkletrees.get_root_leaf()

        previous_block = self.get_last_block()
        next_index = previous_block.index + 1
        previous_hash = previous_block.current_hash

        while not new_block_found:
            cal_hash = calculate_hash(next_index, previous_hash, timestamp, merkleroot, nonce, self.difficulty)

            if cal_hash[0:self.difficulty] == '0' * self.difficulty:
                new_block_attempt = self.generate_block(merkleroot, timestamp, nonce)
                end_timestamp = int(time())
                cos_timestamp = end_timestamp - timestamp
                print '[Info] New block found with nonce ' + str(nonce) + ' in ' + str(
                    round(cos_timestamp, 2)) + ' seconds.'

                # 交易按照timestamp从旧到新（小->大）
                new_block_attempt.transactions = self.current_transactions
                # 将所有交易保存成Merkle树
                new_block_attempt.merkleroot = merkleroot

                db.write_to_db(self.wallet.address, new_block_attempt)
                self.current_transactions = []
                db.clear_unconfirmed_tx_from_disk(self.wallet.address)

                new_block_found = True
            else:
                nonce += 1

        return new_block_attempt

    def get_last_block(self):
        block_height = db.get_block_height(self.wallet.address)
        return db.get_block_data_by_index(self.wallet.address, block_height - 1)

    # def is_same_block(self, block1, block2):
    #     if block1.index != block2.index:
    #         return False
    #     elif block1.previous_hash != block2.previous_hash:
    #         return False
    #     elif block1.timestamp != block2.timestamp:
    #         return False
    #     elif block1.merkleroot != block2.merkleroot:
    #         return False
    #     elif block1.current_hash != block2.current_hash:
    #         return False
    #     return True
    #
    # def __is_valid_new_block(self, new_block, previous_block):
    #     """
    #     1.校验index是否相邻
    #     2.校验hash
    #     :param new_block:
    #     :param previous_block:
    #     :return:
    #     """
    #     new_block_hash = calculate_block_hash(new_block)
    #     if previous_block.index + 1 != new_block.index:
    #         print('Indices Do Not Match Up')
    #         return False
    #     elif previous_block.current_hash != new_block.previous_hash:
    #         print('Previous hash does not match')
    #         return False
    #     elif new_block_hash != new_block.current_hash:
    #         print('Hash is invalid')
    #         return False
    #     return True

    def set_consensus_chain(self):
        # 通过POW机制选取nonce最大的链作为公共链
        for block_index in self.candidate_blocks.keys():
            if block_index <= db.get_block_height(self.get_wallet_address()) - 1:
                curr_block = db.get_block_data_by_index(self.get_wallet_address(), block_index)
                max_nonce_block = curr_block
                for candidate_block in self.candidate_blocks[block_index]:
                    if (candidate_block.previous_hash == curr_block.previous_hash) and (
                                candidate_block.nonce > max_nonce_block.nonce):
                        max_nonce_block = candidate_block

                # 校验每一笔交易
                valid_flag = True
                for idx in range(len(max_nonce_block.transactions)):
                    tx = max_nonce_block.transactions[-1 - idx]
                    if not self.verify_transaction(tx):
                        valid_flag = False

                if valid_flag and max_nonce_block.current_hash != curr_block.current_hash:
                    print '[Info] consensusing, replace with new block', max_nonce_block.current_hash
                    db.write_to_db(self.get_wallet_address(), max_nonce_block)

    def json_output(self):
        output = {
            'wallet_address': self.wallet.address,
            'difficulty': self.difficulty,
            'chain': [block.json_output() for block in db.get_all_blocks(self.wallet.address)],
        }
        return output
