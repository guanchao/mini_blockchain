# coding: utf-8
import ConfigParser
import json
import os
import pickle
from time import time

import pickledb

from Block import Block
from MerkleTrees import MerkleTrees
from script import Script
from transaction import TxInput, TxOutput, Transaction
from util import calculate_hash
from wallet import Wallet


def get_genius_block(index):
    wallet = Wallet()
    txin = TxInput(None, -1, None, None)
    pubkey_hash = Script.sha160(str(wallet.pubkey))
    # txoutput = TxOutput(100, pubkey_hash)
    txoutput = TxOutput(100, "6fef881721b276cfa007f0cf9d0c23114800e8d0")  # 创始区块
    coinbase_tx = Transaction([txin], [txoutput], 1496518102)
    transactions = [coinbase_tx]

    merkletrees = MerkleTrees(transactions)
    merkleroot = merkletrees.get_root_leaf()
    nonce = 0

    genish_block_hash = calculate_hash(index=index,
                                       previous_hash='00000000000000000000000000000000000000000000000000000000000000',
                                       timestamp=1496518102,
                                       merkleroot=merkleroot,
                                       nonce=nonce,
                                       difficulty=4)
    while genish_block_hash[0:4] != '0' * 4:
        genish_block_hash = calculate_hash(index=index,
                                           previous_hash='00000000000000000000000000000000000000000000000000000000000000',
                                           timestamp=1496518102,
                                           merkleroot=merkleroot,
                                           nonce=nonce,
                                           difficulty=4)
        nonce += 1
    genius_block = Block(index=index,
                         previous_hash='00000000000000000000000000000000000000000000000000000000000000',
                         timestamp=1496518102,
                         nonce=nonce,
                         current_hash=genish_block_hash,
                         difficulty=4)
    genius_block.merkleroot = merkleroot
    genius_block.transactions = transactions
    # print 'genius block transactions: ', transactions

    return genius_block


def get_block_height(wallet_address):
    cf = ConfigParser.ConfigParser()
    cf.read(wallet_address + '/miniblockchain.conf')
    block_height = 1
    try:
        block_height = cf.get('meta', 'block_height')
    except ConfigParser.NoSectionError as e:
        pass
    return int(block_height)


def write_unconfirmed_tx_to_db(wallet_address, tx):
    if not os.path.isdir(wallet_address):
        os.mkdir(wallet_address)
    if not os.path.isdir(wallet_address + '/unconfirmed_tx'):
        os.mkdir(wallet_address + '/unconfirmed_tx')

    # 写入到blockheader.db中
    cf = ConfigParser.ConfigParser()
    cf.read(wallet_address + '/miniblockchain.conf')

    unconfirmed_tx_counts = 0
    try:
        unconfirmed_tx_counts = int(cf.get('meta', 'unconfirmed_tx_counts'))
    except ConfigParser.NoOptionError as e:
        cf.set('meta', 'unconfirmed_tx_counts', unconfirmed_tx_counts)

    try:
        # 已存在，不增加高度
        cf.get('unconfirmed_tx_index', str(unconfirmed_tx_counts))
    except ConfigParser.NoSectionError as e:
        cf.add_section('unconfirmed_tx_index')
    except ConfigParser.NoOptionError as e:
        pass

    cf.set('unconfirmed_tx_index', str(unconfirmed_tx_counts), str(tx.txid))
    cf.set('meta', 'unconfirmed_tx_counts', 1 + int(unconfirmed_tx_counts))

    with open(wallet_address + '/miniblockchain.conf', 'w+') as f:
        cf.write(f)

    # 将整个block写入一个文件中
    with open(wallet_address + '/unconfirmed_tx/' + tx.txid, 'wb') as f:
        pickle.dump(tx, f)


def get_all_unconfirmed_tx(wallet_address):
    cf = ConfigParser.ConfigParser()
    cf.read(wallet_address + '/miniblockchain.conf')

    tx_list = list()
    unconfirmed_tx_counts = 0
    try:
        unconfirmed_tx_counts = int(cf.get('meta', 'unconfirmed_tx_counts'))
    except ConfigParser.NoSectionError as e:
        pass
    except ConfigParser.NoOptionError as e:
        pass

    for index in range(unconfirmed_tx_counts):
        txid = cf.get('unconfirmed_tx_index', str(index))
        tx = get_tx_by_txid(wallet_address, txid)
        tx_list.append(tx)

    return tx_list


def get_tx_by_txid(wallet_address, txid):
    with open(wallet_address + '/unconfirmed_tx/' + txid, 'rb') as f:
        obj = pickle.load(f)
    return obj


def clear_unconfirmed_tx_from_disk(wallet_address):
    cf = ConfigParser.ConfigParser()
    cf.read(wallet_address + '/miniblockchain.conf')

    unconfirmed_tx_counts = 0
    try:
        unconfirmed_tx_counts = int(cf.get('meta', 'unconfirmed_tx_counts'))
    except ConfigParser.NoSectionError as e:
        pass

    if unconfirmed_tx_counts == 0:
        return

    for index in range(unconfirmed_tx_counts):
        txid = cf.get('unconfirmed_tx_index', str(index))
        os.remove(wallet_address + '/unconfirmed_tx/' + txid)

    cf.remove_option('meta', 'unconfirmed_tx_counts')
    cf.remove_section('unconfirmed_tx_index')

    with open(wallet_address + '/miniblockchain.conf', 'w+') as f:
        cf.write(f)


def write_to_db(wallet_address, block):
    if not os.path.isdir(wallet_address):
        os.mkdir(wallet_address)
    # 写入到blockheader.db中
    cf = ConfigParser.ConfigParser()
    cf.read(wallet_address + '/miniblockchain.conf')

    block_height = 1
    try:
        block_height = cf.get('meta', 'block_height')
    except ConfigParser.NoSectionError as e:
        cf.add_section('meta')
        cf.set('meta', 'block_height', block_height)

    try:
        # 已存在，不增加高度
        cf.get('index', str(block.index))
    except ConfigParser.NoSectionError as e:
        cf.add_section('index')
    except ConfigParser.NoOptionError as e:
        # 第一次存储，增加高度
        cf.set('meta', 'block_height', 1 + int(block_height))

    cf.set('index', str(block.index), str(block.current_hash))

    with open(wallet_address + '/miniblockchain.conf', 'w+') as f:
        cf.write(f)

    # 将整个block写入一个文件中
    with open(wallet_address + '/' + block.current_hash, 'wb') as f:
        pickle.dump(block, f)


def get_block_hash(wallet_address, index):
    cf = ConfigParser.ConfigParser()
    cf.read(wallet_address + '/miniblockchain.conf')

    block_hash = None
    try:
        block_hash = cf.get('index', str(index))
    except ConfigParser.NoSectionError as e:
        pass
    finally:
        return block_hash


def get_block_data_by_hash(wallet_address, block_hash):
    with open(wallet_address + '/' + block_hash, 'rb') as f:
        obj = pickle.load(f)
        return obj


def get_block_data_by_index(wallet_address, index):
    block_hash = get_block_hash(wallet_address, index)
    return get_block_data_by_hash(wallet_address, block_hash)


def get_all_blocks(wallet_address):
    chain = list()
    block_counts = get_block_height(wallet_address)
    for index in range(block_counts):
        block_hash = get_block_hash(wallet_address, index)
        chain.append(get_block_data_by_hash(wallet_address, block_hash))
    return chain


# txin = TxInput(None, -1, None, None)
# # txoutput = TxOutput(100, pubkey_hash)
# txoutput = TxOutput(100, "6fef881721b276cfa007f0cf9d0c23114800e8d0" + str(int(time())))  # 创始区块
# coinbase_tx = Transaction([txin], [txoutput], time())
#
# write_unconfirmed_tx_to_db('shuwoom', coinbase_tx)

# tx_list = get_all_unconfirmed_tx('shuwoom')
# print [tx.json_output() for tx in tx_list]

# clear_unconfirmed_tx_from_disk('shuwoom')
