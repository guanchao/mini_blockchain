# coding: utf-8
import threading

from p2p import constant


class KNearestNodesUtil(object):
    """
    用于更新保存距离某个节点最近的K个节点
    """

    def __init__(self, node_id, k=constant.K):
        self.k = k
        self.node_id = node_id
        self.list = list()  # 保存更新距离node id最近的k个节点，例如：[(Node obj, boolean)...]
        self.lock = threading.Lock()
        self.target_value = None

    def set_target_value(self, value):
        self.target_value = value

    def get_target_value(self):
        return self.target_value

    def update(self, nodes):
        """
        更新距离key值最近的K个节点
        :param key:
        :return:
        """
        for node in nodes:
            self.__update_node(node)

    def __update_node(self, other_node):
        """
        更新nearest_nodes数据，获取当前node id节点跟other_node的距离，并更新nearest_nodes节点列表
        :param other_node:
        :return:
        """
        if self.node_id == other_node.node_id:
            return
        with self.lock:
            for i in range(len(self.list)):
                node, _ = self.list[i]
                if other_node == node:
                    # other_node已在nearest_nodes中，无需更新
                    break
                if other_node.node_id ^ self.node_id < node.node_id ^ self.node_id:
                    self.list.insert(i, (other_node, False))  # 按最小值从低到高排列节点
                    self.list = self.list[:self.k]  # 取距离最近的前k个节点
                    break
                else:
                    if len(self.list) < self.k:
                        self.list.append((other_node, False))

            if len(self.list) == 0:
                self.list.append((other_node, False))

    def get_unvisited_nearest_nodes(self, alpha):
        if self.target_value:
            return []
        unvisited_nearest_nodes = []
        with self.lock:
            for node, flag in self.list:
                if not flag:
                    unvisited_nearest_nodes.append(node)
                    if len(unvisited_nearest_nodes) >= alpha:
                        break
            return unvisited_nearest_nodes

    def mark(self, visited_node):
        """
        标记node节点已访问过
        :param visited_node:
        :return:
        """
        with self.lock:
            for i in range(len(self.list)):
                node = self.list[i][0]
                if node == visited_node:
                    self.list[i] = (node, True)

    def is_complete(self):
        """
        迭代结束的条件：
        1.找到key值对应的value
        2.找到距离目标节点最近的K个节点（这K个节点都访问过）
        :return:
        """
        with self.lock:
            if self.target_value:
                return True

            if len(self.list) == 0:
                return True

            for node, flag in self.list:
                if not flag:
                    return False
            return True

    def get_result_nodes(self):
        # TODO 有重复
        nodes = list()
        tmp_node_id = list()
        for node, flag in self.list:
            if node.node_id not in tmp_node_id:
                nodes.append(node)
                tmp_node_id.append(node.node_id)
        return nodes
