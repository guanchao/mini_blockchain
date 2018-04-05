# coding: utf-8
import heapq
import threading

import constant

class KBucketSet(object):
    """
    备注：
    bucket中node ID和data key同构，好处：
    1.当hash值空间足够大的时候，随机碰撞可以忽略不计，确保了node ID的唯一性
    2.可以简化路由算法

    参考：https://program-think.blogspot.com/2017/09/Introduction-DHT-Kademlia-Chord.html#head-7
    """
    def __init__(self, current_node_id, k=constant.K, bits=constant.BITS):
        self.node_id = current_node_id
        self.k = k
        self.buckets = [list() for _ in range(bits)]  # 128个k桶
        self.lock = threading.Lock()

    def __is_node_in_bucket(self, node, bucket):
        for peer in bucket:
            if peer == node:
                return True
        return False

    def __node_index_in_bucket(self, node, bucket):
        for i in range(len(bucket)):
            if node == bucket[i]:
                return i
        return -1

    def get_all_nodes(self):
        all_nodes = []
        for bucket in self.buckets:
            for node in bucket:
                all_nodes.append(node)
        return all_nodes


    def insert(self, node):
        """
        往相应的bucket位置插入新节点
        1.如果该bucket没有满且节点不重复，则插入到bucket中
        2.如果该bucket没有满且节点重复，替换该节点
        3.如果该bucket满且节点不重复，则剔除该新节点
        4.如果该bucket满且节点重复，替换该节点

        :param node: <Node obj>
        :return:
        """
        if self.node_id == node.node_id:
            return
        bucket_number = self.get_bucket_number(node.node_id)
        with self.lock:
            bucket = self.buckets[bucket_number]
            if len(bucket) < self.k:  # bucket未满
                if self.__is_node_in_bucket(node, bucket):
                    bucket.pop(self.__node_index_in_bucket(node, bucket))
                bucket.append(node)
            else:  # bucket已满
                if node.triple() in bucket:
                    bucket.pop(self.__node_index_in_bucket(node, bucket))
                else:
                    pass  # 丢弃新节点

    def nearest_nodes(self, node_id):
        """
        获取离node_id节点最近的k个节点（通过最小堆获取）
        :param node_id: 节点id
        :return:
        """
        def get_distance_with_node_id(other_node):
            return node_id ^ other_node.node_id

        with self.lock:
            all_nodes = []
            for bucket in self.buckets:
                for node in bucket:
                    all_nodes.append(node)

            nearest_nodes = heapq.nsmallest(self.k, all_nodes, get_distance_with_node_id)
            return nearest_nodes

    def __get_distance(self, node_id1, node_id2):
        """
        通过异或获取kad中两个节点之间的距离
        :param node_id1:
        :param node_id2:
        :return:
        """
        return node_id1 ^ node_id2

    def get_bucket_number(self, node_id):
        """
        获取目标节点相对于当前节点所在的bucket位置
        :param node_id:
        :return:
        """
        distance = self.__get_distance(self.node_id, node_id)
        length = -1
        while distance:
            distance >>= 1
            length += 1
        return max(0, length)

    def get_bucket(self, bucket_number):
        return self.buckets[bucket_number]

    def exist(self, node_id):
        for bucket in self.buckets:
            for node in bucket:
                if node.node_id == node_id:
                    return True
        return False




