# coding:utf-8
import hashlib
import json
import SocketServer
import threading
import random

import time

from p2p import constant
from p2p.kbucketset import KBucketSet
from p2p.nearestnodes import RPCNearestNodes
from p2p import packet


class RequestHandler(SocketServer.BaseRequestHandler):
    """
    服务端消息处理中心
    """

    def handle(self):
        """
        覆盖实现SocketServer.BaseRequestHandler类的handle方法
        专门接收处理来自服务端的请求

        备注：self.client_address是BaseRequestHandler的成员变量，记录连接到服务端的client地址
        :return:
        """
        msg = json.loads(self.request[0].decode('utf-8').strip())
        print 'Handle from ', self.client_address, msg
        message_type = msg["msg_type"]

        if message_type == packet.MSG_TYPE_PING:
            self.handle_ping(msg)
        elif message_type == packet.MSG_TYPE_PONG:
            self.handle_pong(msg)
        elif message_type == packet.MSG_TYPE_FIND_NEIGHBORS:
            self.handle_find_neighbors(msg)
        elif message_type == packet.MSG_TYPE_FOUND_NEIGHBORS:
            self.handle_found_neighbors(msg)
        elif message_type == packet.MSG_TYPE_FIND_VALUE:
            self.handle_find_value(msg)
        elif message_type == packet.MSG_TYPE_FOUND_VALUE:
            self.handle_found_value(msg)
        elif message_type == packet.MSG_TYPE_STORE:
            self.handle_store(msg)

        client_ip, client_port = self.client_address
        client_node_id = msg['from_id']
        new_node = Node(client_ip, client_port, client_node_id)
        self.server.node_manager.buckets.insert(new_node)

        self.server.node_manager.alive_nodes[client_node_id] = int(time.time()) #更新节点联系时间
        print '[Info] All nodes:', self.server.node_manager.buckets.get_all_nodes()

    def handle_ping(self, message):
        print '[Info] handle ping', message
        socket = self.request[1]
        client_ip, client_port = self.client_address
        client_node_id = message['from_id']

        self.server.node_manager.pong(socket, client_node_id, (client_ip, client_port))

    def handle_pong(self, message):
        print '[Info] handle ping response', message

    def handle_find_neighbors(self, message):
        print '[Info] handle find node', message

        socket = self.request[1]
        client_ip, client_port = self.client_address
        client_node_id = message['from_id']

        node_id = message['target_id']
        rpc_id = message['rpc_id']
        nearest_nodes = self.server.node_manager.buckets.nearest_nodes(node_id)
        if not nearest_nodes:
            nearest_nodes.append(self.server.node_manager.client)
        nearest_nodes_triple = [node.triple() for node in nearest_nodes]
        self.server.node_manager.found_neighbors(node_id, rpc_id, nearest_nodes_triple, socket, client_node_id,
                                                 (client_ip, client_port))

    def handle_found_neighbors(self, message):

        print '[Info] handle find neighbors', message
        rpc_id = message['rpc_id']
        rpc_nearest_nodes = self.server.node_manager.rpc_ids[rpc_id]
        del self.server.node_manager.rpc_ids[rpc_id]
        nearest_nodes = [Node(*node) for node in message['neighbors']]
        rpc_nearest_nodes.update(nearest_nodes)

    def handle_find_value(self, message):
        print '[Info] handle find value', message
        socket = self.request[1]
        client_ip, client_port = self.client_address
        client_node_id = message['from_id']

        key = message['key']
        rpc_id = message['rpc_id']
        if str(key) in self.server.node_manager.data:
            value = self.server.node_manager.data[str(key)]
            self.server.node_manager.found_value(key, value, rpc_id, socket, client_node_id, (client_ip, client_port))
        else:
            nearest_nodes = self.server.node_manager.buckets.nearest_nodes(key)
            if not nearest_nodes:
                nearest_nodes.append(self.server.node_manager.client)
            nearest_nodes_triple = [node.triple() for node in nearest_nodes]
            self.server.node_manager.found_neighbors(key, rpc_id, nearest_nodes_triple, socket, client_node_id,
                                                     (client_ip, client_port))

    def handle_found_value(self, message):
        print '[Info] handle found value', message
        rpc_id = message['rpc_id']
        value = message['value']
        rpc_nearest_nodes = self.server.node_manager.rpc_ids[rpc_id]
        del self.server.node_manager.rpc_ids[rpc_id]
        rpc_nearest_nodes.set_target_value(value)

    def handle_store(self, message):
        print '[Info] handle store', message
        key = message['key']
        value = message['value']
        self.server.node_manager.data[str(key)] = value
        print '[Info] ', self.server.node_manager.client, self.server.node_manager.data


class Server(SocketServer.ThreadingUDPServer):
    """
    接收消息，并做相应处理
    """

    def __init__(self, address, handler):
        SocketServer.UDPServer.__init__(self, address, handler)
        self.lock = threading.Lock()


class Node(object):
    """
    P2P网络的节点，发送消息。实现Kad中的PING、FIND_NODE、FIND_VALUE和STORE消息
    """

    def __init__(self, ip, port, client_node_id):
        self.ip = ip
        self.port = port
        self.node_id = client_node_id

    def __repr__(self):
        return json.dumps(self.__dict__)

    def __eq__(self, other):
        if self.__class__ == other.__class__ \
                and self.ip == other.ip \
                and self.port == other.port \
                and self.node_id == other.node_id:
            return True
        return False

    def triple(self):
        return (self.ip, self.port, self.node_id)

    def __send_message(self, sock, target_node_address, message):
        """

        :param sock: <Socket obj> 跟服务端的socket连接
        :param target_node_address: <tuple> 发送给目标节点的地址(ip,port)
        :param message: <Message obj> 消息对象
        :return:
        """

        message_json_output = json.dumps(message.__dict__)
        sock.sendto(message_json_output, target_node_address)

    def ping(self, sock, target_node_address, message):
        self.__send_message(sock, target_node_address, message)

    def pong(self, sock, target_node_address, message):
        self.__send_message(sock, target_node_address, message)

    def find_neighbors(self, sock, target_node_address, message):
        self.__send_message(sock, target_node_address, message)

    def found_neighbors(self, sock, target_node_address, message):
        self.__send_message(sock, target_node_address, message)

    def find_value(self, sock, target_node_address, message):
        self.__send_message(sock, target_node_address, message)

    def found_value(self, sock, target_node_address, message):
        self.__send_message(sock, target_node_address, message)

    def store(self, sock, target_node_address, message):
        self.__send_message(sock, target_node_address, message)


class NodeManager(object):
    """
    P2P网络中每个节点同时提供Server和Client的作用

    节点之间互相通信(发送+接收)，实现的kad协议算法的4中操作，分别是：
    1.PING：检测节点是否在线
    2.STORE：在某个节点上存储key、value
    3.FIND NODE：返回对方节点桶中距离请求key最近的k个节点
    4.FIND VALUE：与FIND NODE类似，不过返回的是相应key的value

    """

    def __init__(self, ip, port=0, id=None):
        self.ip = ip
        self.port = port
        if not id:
            self.node_id = self.__random_id()
        else:
            self.node_id = id
        self.address = (self.ip, self.port)
        self.buckets = KBucketSet(self.node_id)
        # 每个消息都有一个唯一的rpc_id，用于标识节点之间的通信（该rpc_id由发起方生成，并由接收方返回），
        # 这样可以避免节点收到多个从同一个节点发送的消息时无法区分
        self.rpc_ids = {}  # rpc_ids被多个线程共享，需要加锁

        self.server = Server(self.address, RequestHandler)
        self.port = self.server.server_address[1]
        self.client = Node(self.ip, self.port, self.node_id)
        self.data = {}

        self.alive_nodes = {} # {"xxxx":"2018-03-12 22:00:00",....}

        self.server.node_manager = self

        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

        self.hearbeat_thread = threading.Thread(target=self.hearbeat)
        self.hearbeat_thread.daemon = True
        self.hearbeat_thread.start()

        print '[Info] start new node', self.ip, self.port, self.node_id

    def ping(self, sock, server_node_id, target_node_address):
        msg = packet.Ping(self.node_id, server_node_id)
        print '[Info] send ping'
        self.client.ping(sock, target_node_address, msg)

    def pong(self, sock, server_node_id, target_node_address):
        """
        发送对ping请求的响应消息
        :param sock: Server端监听返回的客户端连接
        :param target_node_address: 目标节点的地址
        :return:
        """
        msg = packet.Pong(self.node_id, server_node_id)
        print '[Info] send pong'
        self.client.pong(sock, target_node_address, msg)

    def find_neighbors(self, node_id, rpc_id, sock, server_node_id, server_node_address):
        msg = packet.FindNeighbors(node_id, self.node_id, server_node_id, rpc_id)
        print '[Info] send find node', packet
        self.client.find_neighbors(sock, server_node_address, msg)

    def found_neighbors(self, node_id, rpc_id, neighbors, sock, server_node_id, server_node_address):

        msg = packet.FoundNeighbors(node_id, self.node_id, server_node_id, rpc_id, neighbors)
        print '[Info] send find neighbors', msg
        self.client.found_neighbors(sock, server_node_address, msg)

    def find_value(self, key, rpc_id, sock, server_node_id, target_node_address):
        msg = packet.FindValue(key, self.node_id, server_node_id, rpc_id)
        print '[Info] send find value', msg
        self.client.find_value(sock, target_node_address, msg)

    def found_value(self, key, value, rpc_id, sock, server_node_id, target_node_address):
        msg = packet.FoundValue(key, value, self.node_id, server_node_id, rpc_id)
        print '[Info] send found value', msg
        self.client.found_value(sock, target_node_address, msg)

    def store(self, key, value, sock, server_node_id, target_node_address):
        msg = packet.Store(key, value, self.node_id, server_node_id)
        print '[Info] send store', msg
        self.client.store(sock, target_node_address, msg)

    def iterative_find_nodes(self, key, seed_node=None):
        """
        找到距离目标节点最近的K个节点
        :param server_node_id:
        :param seed_nodes:
        :return:
        """
        print '[Info] iterative find nodes:', key, seed_node
        rpc_nearest_nodes = RPCNearestNodes(key)
        rpc_nearest_nodes.update(self.buckets.nearest_nodes(key))
        if seed_node:
            rpc_id = self.__get_rpc_id()
            self.rpc_ids[rpc_id] = rpc_nearest_nodes
            self.find_neighbors(key, rpc_id, self.server.socket, key,
                                (seed_node.ip, seed_node.port))

        while (not rpc_nearest_nodes.is_complete()) or seed_node:  # 循环迭代直至距离目标节点最近的K个节点都找出来
            # 限制同时向ALPHA(3)个邻近节点发送FIND NODE请求
            unvisited_nearest_nodes = rpc_nearest_nodes.get_unvisited_nearest_nodes(constant.ALPHA)
            for node in unvisited_nearest_nodes:
                rpc_nearest_nodes.mark(node)
                rpc_id = self.__get_rpc_id()
                self.rpc_ids[rpc_id] = rpc_nearest_nodes
                self.find_neighbors(key, rpc_id, self.server.socket, key,
                                    (node.ip, node.port))
            time.sleep(1)
            seed_node = None

        return rpc_nearest_nodes.get_result_nodes()

    def iterative_find_value(self, key):
        print '[Info] iterative find value:', key
        rpc_nearest_nodes = RPCNearestNodes(key)
        rpc_nearest_nodes.update(self.buckets.nearest_nodes(key))
        while not rpc_nearest_nodes.is_complete():
            # 限制同时向ALPHA(3)个邻近节点发送FIND NODE请求
            unvisited_nearest_nodes = rpc_nearest_nodes.get_unvisited_nearest_nodes(constant.ALPHA)
            for node in unvisited_nearest_nodes:
                rpc_nearest_nodes.mark(node)
                rpc_id = self.__get_rpc_id()
                self.rpc_ids[rpc_id] = rpc_nearest_nodes
                self.find_value(key, rpc_id, self.server.socket, node.node_id, (node.ip, node.port))

            time.sleep(1)

        return rpc_nearest_nodes.get_target_value()

    def bootstrap(self, seed_nodes=[]):
        """
        根据初始节点引导初始化
        :param seed_nodes:<Node list> 种子节点列表
        :return:
        """
        print '[Info] bootstrap', seed_nodes
        for seed_node in seed_nodes:
            self.iterative_find_nodes(self.client.node_id, seed_node)

        if len(seed_nodes) == 0:
            for seed_node in self.buckets.get_all_nodes():
                self.iterative_find_nodes(self.client.node_id, seed_node)

    def __hash_function(self, key):
        return int(hashlib.md5(key.encode('ascii')).hexdigest(), 16)

    def __get_rpc_id(self):
        return random.getrandbits(constant.BITS)

    def __random_id(self):
        return random.randint(0, (2 ** constant.BITS) - 1)

    def hearbeat(self):
        # buckets在15分钟内节点未改变过需要进行refresh操作（对buckets中的每个节点发起find node操作）
        # 如果所有节点都有返回响应，则该buckets不需要经常更新
        # 如果有节点没有返回响应，则该buckets需要定期更新保证buckets的完整性
        while True:
            for bucket in self.buckets.buckets:
                for i in range(len(bucket)):
                    node = bucket[i]
                    node_id = node.node_id
                    ip = node.ip
                    port = node.port

                    tm = int(time.time())
                    if tm - int(self.alive_nodes[node_id]) > 60:
                        # 节点的更新时间超过1min，认为已下线，移除该节点
                        bucket.pop(i)
                        self.alive_nodes.pop(node_id)

                    print '[Info] heartbeat....'
                    self.ping(self.server.socket, node_id, (ip, port))
            time.sleep(10)





    def set_data(self, key, value):
        """
        数据存放:
        1.首先发起节点定位K个距离key最近的节点
        2.发起节点对这K个节点发送STORE消息
        3.收到STORE消息的K个节点保存(key, value)数据

        :param key:
        :param value:
        :return:
        """
        data_key = self.__hash_function(key)
        k_nearest_ndoes = self.iterative_find_nodes(data_key)
        print '[info] set data, k nearest nodes:', k_nearest_ndoes
        if not k_nearest_ndoes:
            self.data[str(data_key)] = value
        for node in k_nearest_ndoes:
            self.store(data_key, value, self.server.socket, node.node_id, (node.ip, node.port))

    def get_data(self, key):
        """
        读取数据
        1.当前节点收到查询数据的请求(获取key对应的value)
        2.当前节点首先检测自己是否保存了该数据，如果有则返回key对应的value
        3.如果当前节点没有保存该数据，则计算获取距离key值最近的K个节点，分别向这K个节点发送FIND VALUE的操作进行查询
        4.收到FIND VALUE请求操作的节点也进行上述(2)~(3)的过程（递归处理）
        :param key:
        :param value:
        :return:
        """
        data_key = self.__hash_function(key)
        if str(data_key) in self.data:
            return self.data[str(data_key)]
        value = self.iterative_find_value(data_key)
        if value:
            return value
        else:
            raise KeyError

