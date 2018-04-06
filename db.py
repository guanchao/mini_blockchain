# coding: utf-8
import ConfigParser
import leveldb
import json
import os
import pickle
from time import time


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
        cf.get('unconfirmed_tx_index', str(unconfirmed_tx_counts))
    except ConfigParser.NoSectionError as e:
        cf.add_section('unconfirmed_tx_index')
    except ConfigParser.NoOptionError as e:
        pass

    cf.set('unconfirmed_tx_index', str(unconfirmed_tx_counts), str(tx.txid))
    cf.set('meta', 'unconfirmed_tx_counts', 1 + int(unconfirmed_tx_counts))

    with open(wallet_address + '/miniblockchain.conf', 'w+') as f:
        cf.write(f)

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
    cf = ConfigParser.ConfigParser()
    cf.read(wallet_address + '/miniblockchain.conf')

    block_height = 1
    try:
        block_height = cf.get('meta', 'block_height')
    except ConfigParser.NoSectionError as e:
        cf.add_section('meta')
        cf.set('meta', 'block_height', block_height)

    try:
        cf.get('index', str(block.index))
    except ConfigParser.NoSectionError as e:
        cf.add_section('index')
    except ConfigParser.NoOptionError as e:
        cf.set('meta', 'block_height', 1 + int(block_height))

    cf.set('index', str(block.index), str(block.current_hash))

    with open(wallet_address + '/miniblockchain.conf', 'w+') as f:
        cf.write(f)

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
