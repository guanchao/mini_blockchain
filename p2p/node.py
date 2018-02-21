# coding:utf-8

import json
import SocketServer
import threading


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

    def __init__(self, message_type, current_node_id=None, target_node_id=None, key=None, value=None):
        self.type = message_type
        self.current_node_id = current_node_id
        self.target_node_id = target_node_id
        self.key = key
        self.value = value

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
        print 'From ', self.client_address
        print message
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
        client_node_id = message['target_node_id']
        new_node = Node(client_ip, client_port, client_node_id)
        # TODO insert new_node into current node's buckets

    def handle_ping(self, message):
        print '[Info] handle ping'
        socket = self.request[1]
        client_ip, client_port = self.client_address
        client_node_id = message['target_node_id']

        node = Node(client_ip, client_port, client_node_id)
        node.ping_response(socket, client_node_id, (client_ip, client_port), Message(Message.MSG_TYPE_PING_RESPONSE))

    def handle_ping_response(self, message):
        print '[Info] handle ping response'

    def handle_find_node(self, message):
        pass

    def handle_find_node_response(self, message):
        pass

    def handle_find_value(self, message):
        pass

    def handle_find_value_response(self, message):
        pass

    def handle_store(self, message):
        pass


class Server(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    """
    接收消息，并做相应处理
    """

    def __init__(self, address, handler):
        SocketServer.UDPServer.__init__(self, address, handler)


class Node(object):
    """
    P2P网络的节点，发送消息。实现Kad中的PING、FIND_NODE、FIND_VALUE和STORE消息
    """

    def __init__(self, ip, port, current_node_id):
        self.ip = ip
        self.port = port
        self.address = (self.ip, self.port)
        self.node_id = current_node_id

    def __send_message(self, sock, target_node_id, target_node_address, message):
        """

        :param sock: <Socket obj> 跟服务端的socket连接
        :param target_node_id: <int> 发送给目标节点的id
        :param target_node_address: <tuple> 发送给目标节点的地址(ip,port)
        :param message: <Message obj> 消息对象
        :return:
        """
        message.current_node_id = self.node_id
        message.target_node_id = target_node_id

        message_json_output = json.dumps(message.__dict__)
        sock.sendto(message_json_output, target_node_address)

    def ping(self, sock, target_node_id, target_node_address, message):
        self.__send_message(sock, target_node_id, target_node_address, message)

    def ping_response(self, sock, target_node_id, target_node_address, message):
        self.__send_message(sock, target_node_id, target_node_address, message)

    def find_node(self, sock, target_node_id, target_node_address, message):
        self.__send_message(sock, target_node_id, target_node_address, message)

    def find_node_response(self, sock, target_node_id, target_node_address, message):
        self.__send_message(sock, target_node_id, target_node_address, message)

    def find_value(self, sock, target_node_id, target_node_address, message):
        self.__send_message(sock, target_node_id, target_node_address, message)

    def find_value_response(self, sock, target_node_id, target_node_address, message):
        self.__send_message(sock, target_node_id, target_node_address, message)

    def store(self, sock, target_node_id, target_node_address, message):
        self.__send_message(sock, target_node_id, target_node_address, message)


class NodeManager(object):
    """
    P2P网络中每个节点同时提供Server和Client的作用

    节点之间互相通信(发送+接收)，实现的kad协议算法的4中操作，分别是：
    1.PING：检测节点是否在线
    2.STORE：在某个节点上存储key、value
    3.FIND NODE：返回对方节点桶中距离请求key最近的k个节点
    4.FIND VALUE：与FIND NODE类似，不过返回的是相应key的value

    """

    def __init__(self, ip, port, id):
        self.ip = ip
        self.port = port
        self.node_id = id
        self.address = (self.ip, self.port)

        self.server = Server(self.address, RequestHandler)
        self.client = Node(ip, port, id)

        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def ping(self, sock, target_node_id, target_node_address):
        message = Message(message_type=Message.MSG_TYPE_PING,
                          current_node_id=self.node_id,
                          target_node_id=target_node_id)
        self.client.ping(sock, target_node_id, target_node_address, message)

    def ping_response(self, sock, target_node_address):
        """
        发送对ping请求的响应消息
        :param sock: Server端监听返回的客户端连接
        :param target_node_address: 目标节点的地址
        :return:
        """
        pass

    def find_node(self, sock, target_node_id, target_node_address):
        message = Message(message_type=Message.MSG_TYPE_FIND_NODE,
                          current_node_id=self.node_id,
                          target_node_id=target_node_id)
        self.client.find_node(sock, target_node_id, target_node_address, message)

    def find_node_response(self, nearest_nodes, sock, target_node_id, target_node_address):
        message = Message(message_type=Message.MSG_TYPE_FIND_NODE_RESPONSE,
                          current_node_id=self.node_id,
                          target_node_id=target_node_id,
                          key="nodes",
                          value=nearest_nodes)
        self.client.find_node_response(sock, target_node_id, target_node_address, message)

    def find_value(self, key, sock, target_node_id, target_node_address):
        message = Message(message_type=Message.MSG_TYPE_FIND_VALUE,
                          current_node_id=self.node_id,
                          target_node_id=target_node_id,
                          key=key)
        self.client.find_value(sock, target_node_id, target_node_address, message)

    def find_value_response(self, key, value, sock, target_node_id, target_node_address):
        message = Message(message_type=Message.MSG_TYPE_FIND_VALUE_RESPONSE,
                          current_node_id=self.node_id,
                          target_node_id=target_node_id,
                          key=key,
                          value=value)
        self.client.find_value_response(sock, target_node_id, target_node_address, message)

    def store(self, key, value, sock, target_node_id, target_node_address):
        message = Message(message_type=Message.MSG_TYPE_STORE,
                          current_node_id=self.node_id,
                          target_node_id=target_node_id,
                          key=key,
                          value=value)
        self.client.store(sock, target_node_id, target_node_address, message)

