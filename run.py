# coding:utf-8
import json
import time, os
import shutil
from flask import Flask, jsonify, request

import db
from p2p.node import NodeManager, Node
from script import Script, get_address_from_ripemd160
from wallet import Wallet

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

"""
简化的区块链

功能：
1.实现P2P(DHT)网络
2.可以进行挖矿
3.可以进行交易
4.可以进行共识

"""

app = Flask(__name__)


# @app.route('/candidates', methods=['GET'])
# def candidates():
#     output = json.dumps(blockchain.candidate_blocks, default=lambda obj: obj.__dict__, indent=4)
#     return output, 200


# @app.route('/ping', methods=['POST'])
# def ping():
#     values = request.get_json()
#     required = ['node_id', 'ip', 'port']
#     if not all(k in values for k in required):
#         return 'Missing values', 400
#
#     node_id = values['node_id']
#     ip = values['ip']
#     port = values['port']
#
#     node_manager.ping(node_manager.server.socket, long(node_id), (str(ip), int(port)))
#     return 'ok', 200


# @app.route('/all_nodes', methods=['GET'])
# def get_all_nodes():
#     all_nodes = node_manager.buckets.get_all_nodes()
#     output = json.dumps(all_nodes, default=lambda obj: obj.__dict__, indent=4)
#     return output, 200


# @app.route('/all_data', methods=['GET'])
# def get_all_data():
#     datas = node_manager.data
#     output = json.dumps(datas, default=lambda obj: obj.__dict__, indent=4)
#     return output, 200


# @app.route('/unconfirmed_tx', methods=['GET'])
# def get_unconfirmed_tx():
#     datas = [tx.json_output() for tx in blockchain.current_transactions]
#     output = json.dumps(datas, default=lambda obj: obj.__dict__, indent=4)
#     return output, 200


@app.route('/bootstrap', methods=['POST'])
def bootstrap():
    values = request.get_json()
    required = ['seeds']
    if not all(k in values for k in required):
        return 'Missing values', 400
    seeds = values['seeds']
    # print json.dumps(seeds, default=lambda obj: obj.__dict__, indent=4)
    seed_nodes = list()
    for seed in seeds:
        seed_nodes.append(Node(seed['ip'], seed['port'], seed['node_id']))
    node_manager.bootstrap(seed_nodes)

    all_nodes = node_manager.buckets.get_all_nodes()
    output = json.dumps(all_nodes, default=lambda obj: obj.__dict__, indent=4)
    return output, 200


@app.route('/curr_node', methods=['GET'])
def curr_node():
    output = {
        'node_id': node_manager.node_id,
        'ip': node_manager.ip,
        'port': node_manager.port,
        'wallet': blockchain.get_wallet_address(),
        'pubkey_hash': Script.sha160(str(blockchain.wallet.pubkey))
    }
    output = json.dumps(output, default=lambda obj: obj.__dict__, indent=4)
    return output, 200



# @app.route('/chain', methods=['GET'])
# def full_chain():
#     output = {
#         'length': db.get_block_height(blockchain.wallet.address),
#         'chain': blockchain.json_output(),
#     }
#     json_output = json.dumps(output, indent=4)
#     return json_output, 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender', 'receiver', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    new_tx = blockchain.new_utxo_transaction(values['sender'], values['receiver'], values['amount'])

    if new_tx:
        # 广播交易
        node_manager.sendtx(new_tx)
        output = {
            'message': 'new transaction been created successfully!',
            'current_transactions': [tx.json_output() for tx in blockchain.current_transactions]
        }
        json_output = json.dumps(output, indent=4)
        return json_output, 200

    else:
        response = {'message': "Not enough funds!"}
        return jsonify(response), 200


@app.route('/balance', methods=['GET'])
def get_balance():
    address = request.args.get('address')
    response = {
        'address': address,
        'balance': blockchain.get_balance_by_db(address)
    }
    return jsonify(response), 200


@app.route('/node_info', methods=['POST'])
def node_info():
    values = request.get_json()
    required = ['ip', 'port']
    if not all(k in values for k in required):
        return 'Missing values', 400

    ip = values['ip']
    port = values['port']
    block_height = db.get_block_height(blockchain.wallet.address)
    latest_block = db.get_block_data_by_index(blockchain.wallet.address, block_height - 1)
    block_hash = latest_block.current_hash
    timestamp = latest_block.timestamp

    time_local = time.localtime(timestamp)

    response = {
        'address': ip + ':' + str(port),
        'block_height': block_height,
        'block_hash': block_hash,
        'wallet_address': blockchain.wallet.address,
        # 'balance': blockchain.get_balance(blockchain.wallet.address),
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S", time_local)
    }
    return jsonify(response), 200


@app.route('/tx_info', methods=['GET'])
def tx_info():
    values = request.get_json()

    block_index = int(request.args.get('block_index'))
    txid = request.args.get('txid')

    block = db.get_block_data_by_index(blockchain.wallet.address, block_index)
    for tx in block.transactions:
        if tx.txid == txid:
            return json.dumps(tx.json_output()), 200

    return 'not exist!', 200


@app.route('/unconfirm_tx_info', methods=['GET'])
def unconfirm_tx_info():
    txid = request.args.get('txid')

    for tx in db.get_all_unconfirmed_tx(blockchain.wallet.address):
        if tx.txid == txid:
            return json.dumps(tx.json_output()), 200

    return 'not exist!', 200


@app.route('/height', methods=['GET'])
def block_height():
    response = {
        'code': 0,
        'value': db.get_block_height(blockchain.wallet.address)
    }
    return json.dumps(response), 200


@app.route('/latest_tx', methods=['GET'])
def latest_tx():
    json_transaction = list()
    for tx in db.get_all_unconfirmed_tx(blockchain.wallet.address):
        txins = tx.txins
        txouts = tx.txouts

        from_addr = list()
        to_addr = list()
        amount = 0
        for txin in txins:
            if txin.prev_tx_out_idx != -1:
                pubkey_hash = Wallet.get_address(txin.pubkey)
                if pubkey_hash not in from_addr:
                    from_addr.append(pubkey_hash)

        for txout in txouts:
            value = txout.value
            script_pub_key = txout.scriptPubKey
            if len(script_pub_key) == 5:
                recv_addr = get_address_from_ripemd160(script_pub_key[2])
                to_addr.append({'receiver': recv_addr, 'value': value})

        new_tx = {
            'txid': tx.txid,
            'senders': from_addr,
            'receivers': to_addr,
            'amount': amount,
            'timestamp': tx.timestamp
        }

        json_transaction.append(new_tx)

    response = {
        'latest_tx': json_transaction
    }
    return json.dumps(response), 200


@app.route('/block_info', methods=['GET'])
def block_info():
    height = request.args.get('height')
    block_index = int(height) - 1

    block = db.get_block_data_by_index(blockchain.wallet.address, block_index)

    json_transaction = list()
    for tx in block.transactions:
        txins = tx.txins
        txouts = tx.txouts

        from_addr = list()
        to_addr = list()
        amount = 0
        for txin in txins:
            if txin.prev_tx_out_idx != -1:
                address = Wallet.get_address(txin.pubkey)
                if address not in from_addr:
                    from_addr.append(address)

        for txout in txouts:
            value = txout.value
            script_pub_key = txout.scriptPubKey
            if len(script_pub_key) == 5:
                recv_addr = get_address_from_ripemd160(script_pub_key[2])
                to_addr.append({'receiver': recv_addr, 'value': value})

        new_tx = {
            'txid': tx.txid,
            'senders': from_addr,
            'receivers': to_addr,
            'amount': amount,
            'timestamp': tx.timestamp
        }

        json_transaction.append(new_tx)

    response = {
        'index': block.index,
        'current_hash': block.current_hash,
        'previous_hash': block.previous_hash,
        'timestamp': block.timestamp,
        'merkleroot': block.merkleroot,
        'difficulty': block.difficulty,
        'nonce': block.nonce,
        'transactions': json_transaction
    }

    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    if port == 5000:
        genisus_node = True
    else:
        genisus_node = False

    node_manager = NodeManager('localhost', 0, genisus_node)
    blockchain = node_manager.blockchain

    print "Wallet address: %s" % blockchain.get_wallet_address()

    app.run(host='0.0.0.0', port=port)
