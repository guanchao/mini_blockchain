# coding:utf-8
import base64
import hashlib, json

from collections import OrderedDict


class MerkleTrees(object):
    def __init__(self, transaction_list=None):
        self.transaction_list = transaction_list
        self.transactions = transaction_list
        self.transaction_tree = OrderedDict()
        self.create_tree()

    def create_tree(self):
        transaction_list = self.transaction_list
        transaction_tree = self.transaction_tree
        temp_transaction = []

        if len(transaction_list) != 1:

            for index in range(0, len(transaction_list), 2):
                left_leaf = transaction_list[index]

                if index + 1 != len(transaction_list):
                    right_leaf = transaction_list[index + 1]
                else:
                    right_leaf = transaction_list[index]

                left_leaf = base64.b64encode(json.dumps(left_leaf))
                right_leaf = base64.b64encode(json.dumps(right_leaf))

                left_leaf_hash = hashlib.sha256(left_leaf).hexdigest()  # 左边叶子节点的哈希值
                right_leaf_hash = hashlib.sha256(right_leaf).hexdigest()  # 右边叶子节点的哈希值

                transaction_tree[left_leaf] = left_leaf_hash
                transaction_tree[right_leaf] = right_leaf_hash

                # parent_hash = hashlib.sha256(left_leaf_hash + right_leaf_hash).hexdigest()
                # temp_transaction.append(parent_hash)
                temp_transaction.append(left_leaf_hash + right_leaf_hash)

            self.transaction_list = temp_transaction
            self.transaction_tree = transaction_tree
            self.create_tree()
        else:
            root_leaf = transaction_list[0]
            root_leaf = base64.b64encode(json.dumps(root_leaf))

            root_leaf_hash = hashlib.sha256(root_leaf).hexdigest()
            transaction_tree[root_leaf] = root_leaf_hash
            self.transaction_tree = transaction_tree

    def get_transaction_tree(self):
        return self.transaction_tree

    def get_transaction_list(self):
        return self.transactions

    def get_root_leaf(self):
        last_key = self.transaction_tree.keys()[-1]
        return self.transaction_tree[last_key]

if __name__ == "__main__":
    # Test
    # transaction = ['aaaa']
    transaction = [{
        'sender': '0000000000000000000000000000000000000000000000000000000000000000',
        'receiver': 123123,
        'amount': 10
    }]
    tree = MerkleTrees(transaction)
    transaction_tree = tree.get_transaction_tree()
    print 'Root of the tree:', tree.get_root_leaf()
    print(json.dumps(transaction_tree, indent=4))
#
#     print '----------------------------------------------'
#
#     transaction = ['aaaa', 'bbbbb', 'ccccc']
#     tree = MerkleTrees(transaction)
#     tree.create_tree()
#     transaction_tree = tree.get_transaction_tree()
#     print 'Root of the tree:', tree.get_root_leaf()
#     print(json.dumps(transaction_tree, indent=4))
