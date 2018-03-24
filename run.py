# coding:utf-8
import json
from binascii import Error

from flask import Flask, jsonify, request

from Blockchain import Blockchain
from p2p.node import NodeManager, Node

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

blockchain = Blockchain()
node_manager = NodeManager('localhost')
print "Wallet address: %s" % blockchain.get_wallet_address()


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
    print json.dumps(seeds, default=lambda obj: obj.__dict__, indent=4)
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
        'port': node_manager.port
    }
    output = json.dumps(output, default=lambda obj: obj.__dict__, indent=4)
    return output, 200


# @app.route('/mine', methods=['GET'])
# def mine():
#     block = blockchain.do_mine()
#     json_output = json.dumps({
#         'message': 'New Block Forged',
#         'index': block.index,
#         'transactions': block.transactions,
#         'merkleroot': block.merkleroot,
#         'nonce': block.nonce,
#         'previous_hash': block.previous_hash
#     }, default=lambda obj: obj.__dict__, sort_keys=True, indent=4)
#     return json_output, 200


@app.route('/chain', methods=['GET'])
def full_chain():
    output = {
        'length': len(blockchain.chain),
        'chain': blockchain.json_output(),
    }
    json_output = json.dumps(output, indent=4)
    return json_output, 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender', 'receiver', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create a new Transaction
    index = blockchain.new_utxo_transaction(values['sender'], values['receiver'], values['amount'])
    if index >= 0:
        try:
            block = blockchain.do_mine()
        except Error, Argument:
            response = {'message': Argument.message}
            return jsonify(response), 200

        output = {
            'message': 'Success! Transaction was added to Block' + str(index),
            'index': block.index,
            'transactions': [tx.json_output() for tx in block.transactions],
            'merkleroot': block.merkleroot,
            'nonce': block.nonce,
            'previous_hash': block.previous_hash
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
        'balance': blockchain.get_balance(address)
    }
    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port
    app.run(host='0.0.0.0', port=port)
