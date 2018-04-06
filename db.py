# coding: utf-8
import ConfigParser
import json
import os
import pickle

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



