# coding:utf-8
import hashlib
from collections import OrderedDict

from transaction import Transaction


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

                left_leaf = left_leaf.txid
                right_leaf = right_leaf.txid

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
            if isinstance(root_leaf, Transaction):
                root_leaf = root_leaf.txid
            else:
                root_leaf = root_leaf

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

    def find_unspent_transactions(self, address):
        for transaction in self.get_transaction_list():
            print transaction

    def find_spendalbe_outputs(self, from_addr, amount):
        for block in self.chain:
            print block


# if __name__ == "__main__":
#     transactions = []
#     input = TxInput(None, -1, "Reward to 123456")
#     output = TxOutput(10, "123456")
#     print str(input)
#     print str(output)
#
#     tx = Transaction([input], [output])
#     transactions.append(tx)
#     print str(tx)
#
#     tree = MerkleTrees(transactions)
#     transaction_tree = tree.get_transaction_tree()
#     print 'Root of the tree:', tree.get_root_leaf()
#     print(json.dumps(transaction_tree, indent=4))
# #
#     print '----------------------------------------------'
#     tx2 = Transaction([TxInput(None, -1, "Reward to 654321")], [TxOutput(20, "654321")])
#     transactions.append(tx2)
#     tree2 = MerkleTrees(transactions)
#     tree2.create_tree()
#     transaction_tree2 = tree2.get_transaction_tree()
#     print 'Root of the tree:', tree2.get_root_leaf()
#     print(json.dumps(transaction_tree2, indent=4))
#
#     print str(tx)
