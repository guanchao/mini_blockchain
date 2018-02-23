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


class Message(object):
    """
    P2P节点中互相通信的用的消息对象
    """
    MSG_TYPE_PING = 101
    MSG_TYPE_PING_RESPONSE = 102

    MSG_TYPE_FIND_NODE = 103
    MSG_TYPE_FIND_NODE_RESPONSE = 104

    MSG_TYPE_FIND_VALUE = 105
    MSG_TYPE_FIND_VALUE_RESPONSE = 106

    MSG_TYPE_STORE = 107

    def __init__(self, message_type, client_node_id=None, server_node_id=None, key=None, value=None, node_id=None,
                 rpc_id=None, nearest_nodes=None):
        self.type = message_type
        self.client_node_id = client_node_id
        self.server_node_id = server_node_id
        self.key = key
        self.value = value
        self.node_id = node_id
        self.rpc_id = rpc_id
        self.nearest_nodes = nearest_nodes

    def __repr__(self):
        return json.dumps(self.__dict__)


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
        message = json.loads(self.request[0].decode('utf-8').strip())
        print 'From ', self.client_address, message
        message_type = message["type"]

        if message_type == Message.MSG_TYPE_PING:
            self.handle_ping(message)
        elif message_type == Message.MSG_TYPE_PING_RESPONSE:
            self.handle_ping_response(message)
        elif message_type == Message.MSG_TYPE_FIND_NODE:
            self.handle_find_node(message)
        elif message_type == Message.MSG_TYPE_FIND_NODE_RESPONSE:
            self.handle_find_node_response(message)
        elif message_type == Message.MSG_TYPE_FIND_VALUE:
            self.handle_find_value(message)
        elif message_type == Message.MSG_TYPE_FIND_VALUE_RESPONSE:
            self.handle_find_value_response(message)
        elif message_type == Message.MSG_TYPE_STORE:
            self.handle_store(message)

        client_ip, client_port = self.client_address
        client_node_id = message['client_node_id']
        new_node = Node(client_ip, client_port, client_node_id)
        self.server.node_manager.buckets.insert(new_node)
        print '[Info] All nodes:', self.server.node_manager.buckets.get_all_nodes()

    def handle_ping(self, message):
        print '[Info] handle ping', message
        socket = self.request[1]
        client_ip, client_port = self.client_address
        client_node_id = message['client_node_id']

        self.server.node_manager.ping_response(socket, client_node_id, (client_ip, client_port))

    def handle_ping_response(self, message):
        print '[Info] handle ping response', message

    def handle_find_node(self, message):
        print '[Info] handle find node', message

        socket = self.request[1]
        client_ip, client_port = self.client_address
        client_node_id = message['client_node_id']

        node_id = message['node_id']
        rpc_id = message['rpc_id']
        nearest_nodes = self.server.node_manager.buckets.nearest_nodes(node_id)
        if not nearest_nodes:
            nearest_nodes.append(self.server.node_manager.client)
        nearest_nodes_triple = [node.triple() for node in nearest_nodes]
        self.server.node_manager.find_node_response(node_id, rpc_id, nearest_nodes_triple, socket, client_node_id,
                                                    (client_ip, client_port))

    def handle_find_node_response(self, message):
        print '[Info] handle find node response', message
        rpc_id = message['rpc_id']
        rpc_nearest_nodes = self.server.node_manager.rpc_ids[rpc_id]
        print '[Info] handle find node response:', rpc_nearest_nodes.list
        del self.server.node_manager.rpc_ids[rpc_id]
        nearest_nodes = [Node(*node) for node in message['nearest_nodes']]
        print '[Info] handle find node response, update new nodes:', nearest_nodes
        rpc_nearest_nodes.update(nearest_nodes)
        print '[Info] handle find node response, after new nodes:', rpc_nearest_nodes.list

    def handle_find_value(self, message):
        print '[Info] handle find value', message

    def handle_find_value_response(self, message):
        print '[Info] handle find value response', message

    def handle_store(self, message):
        print '[Info] handle store', message


class Server(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
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

    def __send_message(self, sock, server_node_id, target_node_address, message):
        """

        :param sock: <Socket obj> 跟服务端的socket连接
        :param server_node_id: <int> 发送给目标节点的id
        :param target_node_address: <tuple> 发送给目标节点的地址(ip,port)
        :param message: <Message obj> 消息对象
        :return:
        """
        message.client_node_id = self.node_id
        message.server_node_id = server_node_id

        message_json_output = json.dumps(message.__dict__)
        sock.sendto(message_json_output, target_node_address)

    def ping(self, sock, server_node_id, target_node_address, message):
        self.__send_message(sock, server_node_id, target_node_address, message)

    def ping_response(self, sock, server_node_id, target_node_address, message):
        self.__send_message(sock, server_node_id, target_node_address, message)

    def find_node(self, sock, target_node_id, target_node_address, message):
        self.__send_message(sock, target_node_id, target_node_address, message)

    def find_node_response(self, sock, target_node_id, target_node_address, message):
        self.__send_message(sock, target_node_id, target_node_address, message)

    def find_value(self, sock, server_node_id, target_node_address, message):
        self.__send_message(sock, server_node_id, target_node_address, message)

    def find_value_response(self, sock, server_node_id, target_node_address, message):
        self.__send_message(sock, server_node_id, target_node_address, message)

    def store(self, sock, server_node_id, target_node_address, message):
        self.__send_message(sock, server_node_id, target_node_address, message)


class NodeManager(object):
    """
    P2P网络中每个节点同时提供Server和Client的作用

    节点之间互相通信(发送+接收)，实现的kad协议算法的4中操作，分别是：
    1.PING：检测节点是否在线
    2.STORE：在某个节点上存储key、value
    3.FIND NODE：返回对方节点桶中距离请求key最近的k个节点
    4.FIND VALUE：与FIND NODE类似，不过返回的是相应key的value

    """

    def __init__(self, ip, port, id=None):
        self.ip = ip
        self.port = port
        if not id:
            self.node_id = self.__random_id()
        else:
            self.node_id = id
        self.address = (self.ip, self.port)
        self.buckets = KBucketSet(self.node_id)
        self.rpc_ids = {}

        self.server = Server(self.address, RequestHandler)
        self.client = Node(ip, port, self.node_id)

        self.server.node_manager = self

        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        print '[Info] start new node', self.ip, self.port, self.node_id

    def ping(self, sock, server_node_id, target_node_address):
        message = Message(message_type=Message.MSG_TYPE_PING,
                          client_node_id=self.node_id,
                          server_node_id=server_node_id)
        print '[Info] send ping'
        self.client.ping(sock, server_node_id, target_node_address, message)

    def ping_response(self, sock, server_node_id, target_node_address):
        """
        发送对ping请求的响应消息
        :param sock: Server端监听返回的客户端连接
        :param target_node_address: 目标节点的地址
        :return:
        """
        message = Message(message_type=Message.MSG_TYPE_PING_RESPONSE,
                          client_node_id=self.node_id,
                          server_node_id=server_node_id)
        print '[Info] send ping response'
        self.client.ping_response(sock, server_node_id, target_node_address, message)

    def find_node(self, node_id, rpc_id, sock, server_node_id, server_node_address):
        message = Message(message_type=Message.MSG_TYPE_FIND_NODE,
                          client_node_id=node_id,
                          server_node_id=server_node_id,
                          node_id=node_id,
                          rpc_id=rpc_id)
        print '[Info] send find node', message
        self.client.find_node(sock, server_node_id, server_node_address, message)

    def find_node_response(self, node_id, rpc_id, nearest_nodes, sock, server_node_id, servernode_address):
        message = Message(message_type=Message.MSG_TYPE_FIND_NODE_RESPONSE,
                          client_node_id=self.node_id,
                          server_node_id=server_node_id,
                          key=node_id,
                          rpc_id=rpc_id,
                          nearest_nodes=nearest_nodes)
        print '[Info] send find node response', message
        self.client.find_node_response(sock, server_node_id, servernode_address, message)

    def find_value(self, key, sock, server_node_id, target_node_address):
        message = Message(message_type=Message.MSG_TYPE_FIND_VALUE,
                          client_node_id=self.node_id,
                          server_node_id=server_node_id,
                          key=key)
        self.client.find_value(sock, server_node_id, target_node_address, message)

    def find_value_response(self, key, value, sock, server_node_id, target_node_address):
        message = Message(message_type=Message.MSG_TYPE_FIND_VALUE_RESPONSE,
                          client_node_id=self.node_id,
                          server_node_id=server_node_id,
                          key=key,
                          value=value)
        self.client.find_value_response(sock, server_node_id, target_node_address, message)

    def store(self, key, value, sock, server_node_id, target_node_address):
        message = Message(message_type=Message.MSG_TYPE_STORE,
                          client_node_id=self.node_id,
                          server_node_id=server_node_id,
                          key=key,
                          value=value)
        self.client.store(sock, server_node_id, target_node_address, message)

    def iterative_find_nodes(self, target_node, seed_node=None):
        """
        找到距离目标节点最近的K个节点
        :param server_node_id:
        :param seed_nodes:
        :return:
        """
        print '[Info] iterative find nodes:', target_node, seed_node
        rpc_nearest_nodes = RPCNearestNodes(target_node.node_id)
        rpc_nearest_nodes.update(self.buckets.nearest_nodes(target_node.node_id))
        print '[Info] first rpc nearest nodes', rpc_nearest_nodes.list
        if seed_node:
            rpc_id = self.__get_rpc_id()
            self.rpc_ids[rpc_id] = rpc_nearest_nodes
            self.find_node(target_node.node_id, rpc_id, self.server.socket, target_node.node_id,
                           (seed_node.ip, seed_node.port))
            # time.sleep(5)
        while (not rpc_nearest_nodes.is_complete()) or seed_node:  # 循环迭代直至距离目标节点最近的K个节点都找出来
            # 限制同时向ALPHA(3)个邻近节点发送FIND NODE请求
            unvisited_nearest_nodes = rpc_nearest_nodes.get_unvisited_nearest_nodes(constant.ALPHA)
            print '[Info] unvisited nearest nodes', unvisited_nearest_nodes
            for node in unvisited_nearest_nodes:
                rpc_nearest_nodes.mark(node)
                rpc_id = self.__get_rpc_id()
                self.rpc_ids[rpc_id] = rpc_nearest_nodes
                self.find_node(target_node.node_id, rpc_id, self.server.socket, target_node.node_id,
                               (node.ip, node.port))
            time.sleep(1)
            seed_node = None

        return rpc_nearest_nodes.get_result_nodes()

    def bootstrap(self, seed_nodes=[]):
        """
        根据初始节点引导初始化
        :param seed_nodes:<Node list> 种子节点列表
        :return:
        """
        print '[Info] bootstrap', seed_nodes
        for seed_node in seed_nodes:
            self.iterative_find_nodes(self.client, seed_node)

        if len(seed_nodes) == 0:
            for seed_node in self.buckets.get_all_nodes():
                self.iterative_find_nodes(self.client, seed_node)

    def __hash_function(self, key):
        return int(hashlib.md5(key.encode('ascii')).hexdigest(), 16)

    def __get_rpc_id(self):
        return random.getrandbits(constant.BITS)

    def __random_id(self):
        return random.randint(0, (2 ** constant.BITS) - 1)

    def __get_nearest_nodes(self, data_key):
        self.buckets.update_nearest_nodes(data_key)

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

    def get_data(self, key, value):
        """
        读取数据
        :param key:
        :param value:
        :return:
        """
        pass
