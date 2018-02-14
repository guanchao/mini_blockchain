# coding:utf-8
import hashlib, json

from collections import OrderedDict


class MerkleTrees(object):
    def __init__(self, transaction_list=None):
        self.transaction_list = transaction_list
        self.transaction_tree = OrderedDict()

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
            root_leaf_hash = hashlib.sha256(root_leaf).hexdigest()
            transaction_tree[transaction_list[0]] = root_leaf_hash
            self.transaction_tree = transaction_tree


    def get_transaction_tree(self):
        return self.transaction_tree

    def get_root_leaf(self):
        last_key = self.transaction_tree.keys()[-1]
        return self.transaction_tree[last_key]

if __name__ == "__main__":
    # Test
    transaction = ['a', 'b']
    tree = MerkleTrees(transaction)
    tree.create_tree()
    transaction_tree = tree.get_transaction_tree()
    print 'Root of the tree:', tree.get_root_leaf()
    print(json.dumps(transaction_tree, indent=4))

    print '----------------------------------------------'

    transaction = ['a', 'b', 'c']
    tree = MerkleTrees(transaction)
    tree.create_tree()
    transaction_tree = tree.get_transaction_tree()
    print 'Root of the tree:', tree.get_root_leaf()
    print(json.dumps(transaction_tree, indent=4))

