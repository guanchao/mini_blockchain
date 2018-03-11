# coding:utf-8
import json
from flask import Flask, jsonify, request

from Blockchain import Blockchain

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
print "Node id: %s" % blockchain.node_id


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
    json_output = json.dumps({
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }, default=lambda obj: obj.__dict__, sort_keys=True, indent=4)
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
        block = blockchain.do_mine()
        json_output = json.dumps({
            'message': 'Success! Transaction was added to Block' + str(index),
            'index': block.index,
            'transactions': block.transactions,
            'merkleroot': block.merkleroot,
            'nonce': block.nonce,
            'previous_hash': block.previous_hash
        }, default=lambda obj: obj.__dict__, indent=4)
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
