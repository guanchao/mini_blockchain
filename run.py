# coding:utf-8
import json
import time

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
1.可以进行挖矿
2.可以进行交易
3.可以进行简单工作量证明
4.可以进行简单共识


TODO:
1.POW机制扩展
2.共识扩展
3.p2p网络发现

"""

app = Flask(__name__)

node_manager = NodeManager('localhost')
blockchain = node_manager.blockchain

print "Wallet address: %s" % blockchain.get_wallet_address()


@app.route('/candidates', methods=['GET'])
def candidates():
    output = json.dumps(blockchain.candidate_blocks, default=lambda obj: obj.__dict__, indent=4)
    return output, 200


@app.route('/ping', methods=['POST'])
def ping():
    values = request.get_json()
    required = ['node_id', 'ip', 'port']
    if not all(k in values for k in required):
        return 'Missing values', 400

    node_id = values['node_id']
    ip = values['ip']
    port = values['port']

    node_manager.ping(node_manager.server.socket, long(node_id), (str(ip), int(port)))
    return 'ok', 200


@app.route('/all_nodes', methods=['GET'])
def get_all_nodes():
    all_nodes = node_manager.buckets.get_all_nodes()
    output = json.dumps(all_nodes, default=lambda obj: obj.__dict__, indent=4)
    return output, 200


@app.route('/all_data', methods=['GET'])
def get_all_data():
    datas = node_manager.data
    output = json.dumps(datas, default=lambda obj: obj.__dict__, indent=4)
    return output, 200


@app.route('/unconfirmed_tx', methods=['GET'])
def get_unconfirmed_tx():
    datas = [tx.json_output() for tx in blockchain.current_transactions]
    output = json.dumps(datas, default=lambda obj: obj.__dict__, indent=4)
    return output, 200


@app.route('/set_data', methods=['POST'])
def set_data():
    values = request.get_json()
    required = ['key', 'value']
    if not all(k in values for k in required):
        return 'Missing values', 400
    key = values['key']
    value = values['value']
    node_manager.set_data(key, value)

    datas = node_manager.data
    output = json.dumps(datas, default=lambda obj: obj.__dict__, indent=4)
    return output, 200


@app.route('/get_data', methods=['GET'])
def get_data():
    key = request.args.get('key')
    try:
        value = node_manager.get_data(key)
        return value, 200
    except KeyError as e:
        return 'not found!', 200


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


#
# @app.route('/mine', methods=['GET'])
# def mine():
#     try:
#         block = blockchain.do_mine()
#     except Error, Argument:
#         response = {'message': Argument.message}
#         return jsonify(response), 200
#
#     output = {
#         'message': 'Contrigulations, Find new block!',
#         'index': block.index,
#         'transactions': [tx.json_output() for tx in block.transactions],
#         'merkleroot': block.merkleroot,
#         'nonce': block.nonce,
#         'previous_hash': block.previous_hash
#     }
#     json_output = json.dumps(output, indent=4)
#     return json_output, 200


@app.route('/chain', methods=['GET'])
def full_chain():
    output = {
        'length': db.get_block_height(blockchain.wallet.address),
        'chain': blockchain.json_output(),
    }
    json_output = json.dumps(output, indent=4)
    return json_output, 200


@app.route('/candidate_blocks', methods=['GET'])
def candidate_blocks():
    # output = {
    #     'length': len(blockchain.candidate_blocks),
    #     'candidate_blocks': [block.json_output() for block in blockchain.candidate_blocks],
    # }
    for block_index in blockchain.candidate_blocks.keys():
        for candidate_block in blockchain.candidate_blocks[block_index]:
            print block_index, candidate_block.current_hash, candidate_block.nonce
    # json_output = json.dumps(output, indent=4)
    # return json_output, 200
    return 'ok', 200


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
        print '[++++++++++++] sendtx', new_tx.txid
        output = {
            'message': 'new transaction been created successfully!',
            'current_transactions': [tx.json_output() for tx in blockchain.current_transactions]
        }
        json_output = json.dumps(output, indent=4)
        return json_output, 200
    # try:
    #         block = blockchain.do_mine()
    #     except Error, Argument:
    #         response = {'message': Argument.message}
    #         return jsonify(response), 200
    #
    #     output = {
    #         'message': 'Success! Transaction was added to Block' + str(index),
    #         'index': block.index,
    #         'transactions': [tx.json_output() for tx in block.transactions],
    #         'merkleroot': block.merkleroot,
    #         'nonce': block.nonce,
    #         'previous_hash': block.previous_hash
    #     }
    #     json_output = json.dumps(output, indent=4)
    #     return json_output, 200
    #
    else:
        response = {'message': "Not enough funds!"}
        return jsonify(response), 200


@app.route('/balance', methods=['GET'])
def get_balance(): # TODO
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
    latest_block = db.get_block_data_by_index(blockchain.wallet.address, block_height-1)
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
    app.run(host='0.0.0.0', port=port)
