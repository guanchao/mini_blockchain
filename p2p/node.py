# coding:utf-8
import hashlib
import json
import SocketServer
import pickle
import threading
import random

import time
from binascii import Error

import zlib

import db
from blockchain import Blockchain
from p2p import constant
from p2p.kbucketset import KBucketSet
from p2p.nearestnodes import RPCNearestNodes
from p2p import packet
from p2p.packet import Version, Verack


class ProcessMessages(SocketServer.BaseRequestHandler):
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
        msg_obj = pickle.loads(zlib.decompress(self.request[0]))
        command = msg_obj.command
        payload = msg_obj.payload

        # print 'Handle ', command, 'from ', self.client_address
        # print command, 'payload:', payload

        if command == "ping":
            self.handle_ping(payload)
        elif command == "pong":
            self.handle_pong(payload)
        elif command == "find_neighbors":
            self.handle_find_neighbors(payload)
        elif command == "found_neighbors":
            self.handle_found_neighbors(payload)
        elif command == "find_value":
            self.handle_find_value(payload)
        elif command == "found_value":
            self.handle_found_value(payload)
        elif command == "store":
            self.handle_store(payload)
        elif command == "sendtx":
            self.handle_sendtx(payload)
        elif command == "sendblock":
            self.handle_sendblock(payload)
        elif command == "version":
            self.handle_version(payload)
        elif command == "verack":
            self.handle_verack(payload)

            # client_node_id = payload.from_id
            # if self.server.node_manager.buckets.exist(client_node_id):
            #     self.server.node_manager.alive_nodes[client_node_id] = int(time.time())  # 更新节点联系时间

    def handle_ping(self, payload):
        socket = self.request[1]
        client_ip, client_port = self.client_address
        client_node_id = payload.from_id

        self.server.node_manager.pong(socket, client_node_id, (client_ip, client_port))

    def handle_pong(self, payload):
        pass

    def handle_find_neighbors(self, payload):
        socket = self.request[1]
        client_ip, client_port = self.client_address
        client_node_id = payload.from_id

        node_id = payload.target_id
        rpc_id = payload.rpc_id
        nearest_nodes = self.server.node_manager.buckets.nearest_nodes(node_id)
        if not nearest_nodes:
            nearest_nodes.append(self.server.node_manager.client)
        nearest_nodes_triple = [node.triple() for node in nearest_nodes]
        self.server.node_manager.found_neighbors(node_id, rpc_id, nearest_nodes_triple, socket, client_node_id,
                                                 (client_ip, client_port))

    def handle_found_neighbors(self, payload):
        rpc_id = payload.rpc_id
        rpc_nearest_nodes = self.server.node_manager.rpc_ids[rpc_id]
        del self.server.node_manager.rpc_ids[rpc_id]
        nearest_nodes = [Node(*node) for node in payload.neighbors]
        rpc_nearest_nodes.update(nearest_nodes)

    def handle_find_value(self, payload):
        socket = self.request[1]
        client_ip, client_port = self.client_address
        client_node_id = payload.from_id

        key = payload.key
        rpc_id = payload.rpc_id
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

    def handle_found_value(self, payload):
        rpc_id = payload.rpc_id
        value = payload.value
        rpc_nearest_nodes = self.server.node_manager.rpc_ids[rpc_id]
        del self.server.node_manager.rpc_ids[rpc_id]
        rpc_nearest_nodes.set_target_value(value)

    def handle_store(self, payload):
        key = payload.key
        value = payload.value
        self.server.node_manager.data[str(key)] = value

    def handle_sendtx(self, payload):
        new_tx = payload
        with self.server.node_manager.lock:
            blockchain = self.server.node_manager.blockchain

            # 判断区块中是否存在
            if blockchain.find_transaction(new_tx.txid):
                return
            # 判断交易池中是否存在
            for k in range(len(blockchain.current_transactions)):
                uncomfirmed_tx = blockchain.current_transactions[-1 - k]
                if uncomfirmed_tx.txid == new_tx.txid:
                    return

            blockchain.current_transactions.append(new_tx)
            db.write_unconfirmed_tx_to_db(blockchain.wallet.address, new_tx)

    def handle_sendblock(self, payload):
        new_block = payload
        with self.server.node_manager.lock:
            blockchain = self.server.node_manager.blockchain
            block_height = db.get_block_height(blockchain.wallet.address)
            latest_block = db.get_block_data_by_index(blockchain.get_wallet_address(), block_height - 1)

            if (latest_block.current_hash == new_block.previous_hash) and (latest_block.index + 1 == new_block.index):

                # 校验交易是否有效
                is_valid = True
                for idx in range(len(new_block.transactions)):
                    tx = new_block.transactions[-1 - idx]
                    if not blockchain.verify_transaction(tx):
                        is_valid = False
                        break

                if is_valid:
                    db.write_to_db(blockchain.wallet.address, new_block)
                    # 重新挖矿
                    blockchain.current_transactions = []
                    db.clear_unconfirmed_tx_from_disk(blockchain.wallet.address)
            else:
                self.add_to_candidate_blocks(blockchain, new_block)

            blockchain.set_consensus_chain()

    def handle_version(self, payload):
        version = payload.version
        if version != 1:
            # 版本不一样，拒绝
            print '[Warn] invalid version, ignore!!'
            pass
        else:
            client_ip, client_port = self.client_address
            client_node_id = payload.from_id
            new_node = Node(client_ip, client_port, client_node_id)
            new_node.version = 1
            self.server.node_manager.buckets.insert(new_node)
            blockchain = self.server.node_manager.blockchain

            block_counts = db.get_block_height(blockchain.get_wallet_address())
            verack = Verack(1, int(time.time()), self.server.node_manager.node_id, client_node_id,
                            block_counts)
            self.server.node_manager.sendverck(new_node, verack)

            if payload.best_height > block_counts:
                # TODO 检查best_height，同步区块链
                pass

    def handle_verack(self, payload):
        version = payload.version
        if version != 1:
            # 版本不一样，拒绝
            print '[Warn] invalid version, ignore!!'
            pass
        else:
            client_node_id = payload.from_id
            client_ip, client_port = self.client_address
            new_node = Node(client_ip, client_port, client_node_id)
            new_node.version = 1
            self.server.node_manager.buckets.insert(new_node)
            blockchain = self.server.node_manager.blockchain

            if payload.best_height > db.get_block_height(blockchain.get_wallet_address()):
                # TODO 检查best_height，同步区块链
                pass

    def add_to_candidate_blocks(self, blockchain, new_block):
        if new_block.index in blockchain.candidate_blocks.keys():
            blockchain.candidate_blocks[new_block.index].add(new_block)
        else:
            blockchain.candidate_blocks[new_block.index] = set()
            blockchain.candidate_blocks[new_block.index].add(new_block)


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
        self.version = None

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

    def ping(self, sock, target_node_address, message):
        sock.sendto(zlib.compress(message), target_node_address)

    def pong(self, sock, target_node_address, message):
        sock.sendto(zlib.compress(message), target_node_address)

    def find_neighbors(self, sock, target_node_address, message):
        sock.sendto(zlib.compress(message), target_node_address)

    def found_neighbors(self, sock, target_node_address, message):
        sock.sendto(zlib.compress(message), target_node_address)

    def find_value(self, sock, target_node_address, message):
        sock.sendto(zlib.compress(message), target_node_address)

    def found_value(self, sock, target_node_address, message):
        sock.sendto(zlib.compress(message), target_node_address)

    def store(self, sock, target_node_address, message):
        sock.sendto(zlib.compress(message), target_node_address)

    def sendtx(self, sock, target_node_address, message):
        ret = sock.sendto(zlib.compress(message), target_node_address)

    def sendblock(self, sock, target_node_address, message):
        ret = sock.sendto(zlib.compress(message), target_node_address)

    def sendversion(self, sock, target_node_address, message):
        sock.sendto(zlib.compress(message), target_node_address)

    def sendverack(self, sock, target_node_address, message):
        sock.sendto(zlib.compress(message), target_node_address)


class NodeManager(object):
    """
    P2P网络中每个节点同时提供Server和Client的作用

    节点之间互相通信(发送+接收)，实现的kad协议算法的4中操作，分别是：
    1.PING：检测节点是否在线
    2.STORE：在某个节点上存储key、value
    3.FIND NODE：返回对方节点桶中距离请求key最近的k个节点
    4.FIND VALUE：与FIND NODE类似，不过返回的是相应key的value

    """

    def __init__(self, ip, port=0, genisus_node=False):
        self.ip = ip
        self.port = port
        self.node_id = self.__random_id()
        self.address = (self.ip, self.port)
        self.buckets = KBucketSet(self.node_id)
        # 每个消息都有一个唯一的rpc_id，用于标识节点之间的通信（该rpc_id由发起方生成，并由接收方返回），
        # 这样可以避免节点收到多个从同一个节点发送的消息时无法区分
        self.rpc_ids = {}  # rpc_ids被多个线程共享，需要加锁

        self.lock = threading.Lock()  # 备注，由于blockchain数据被多个线程共享使用（矿工线程、消息处理线程），需要加锁

        self.server = Server(self.address, ProcessMessages)
        self.port = self.server.server_address[1]
        self.client = Node(self.ip, self.port, self.node_id)
        self.data = {}

        self.alive_nodes = {}  # {"xxxx":"2018-03-12 22:00:00",....}

        self.server.node_manager = self
        self.blockchain = Blockchain(genisus_node)

        # 消息处理
        self.processmessages_thread = threading.Thread(target=self.server.serve_forever)
        self.processmessages_thread.daemon = True
        self.processmessages_thread.start()

        # 消息发送 TODO
        # self.sendmessages_thread = threading.Thread(target=self.sendmessages)
        # self.sendmessages_thread.daemon = True
        # self.sendmessages_thread.start()

        # 矿工线程
        self.minner_thread = threading.Thread(target=self.minner)
        self.minner_thread.daemon = True
        self.minner_thread.start()

        print '[Info] start new node', self.ip, self.port, self.node_id

    def ping(self, sock, server_node_id, target_node_address):
        payload = packet.Ping(self.node_id, server_node_id)
        msg_obj = packet.Message("ping", payload)
        msg_bytes = pickle.dumps(msg_obj)
        self.client.ping(sock, target_node_address, msg_bytes)

    def pong(self, sock, server_node_id, target_node_address):
        """
        发送对ping请求的响应消息
        :param sock: Server端监听返回的客户端连接
        :param target_node_address: 目标节点的地址
        :return:
        """
        payload = packet.Pong(self.node_id, server_node_id)
        msg_obj = packet.Message("pong", payload)
        msg_bytes = pickle.dumps(msg_obj)
        self.client.pong(sock, target_node_address, msg_bytes)

    def find_neighbors(self, node_id, rpc_id, sock, server_node_id, server_node_address):
        payload = packet.FindNeighbors(node_id, self.node_id, server_node_id, rpc_id)
        msg_obj = packet.Message("find_neighbors", payload)
        msg_bytes = pickle.dumps(msg_obj)
        self.client.find_neighbors(sock, server_node_address, msg_bytes)

    def found_neighbors(self, node_id, rpc_id, neighbors, sock, server_node_id, server_node_address):
        payload = packet.FoundNeighbors(node_id, self.node_id, server_node_id, rpc_id, neighbors)
        msg_obj = packet.Message("found_neighbors", payload)
        msg_bytes = pickle.dumps(msg_obj)
        self.client.found_neighbors(sock, server_node_address, msg_bytes)

    def find_value(self, key, rpc_id, sock, server_node_id, target_node_address):
        payload = packet.FindValue(key, self.node_id, server_node_id, rpc_id)
        msg_obj = packet.Message("find_value", payload)
        msg_bytes = pickle.dumps(msg_obj)
        self.client.find_value(sock, target_node_address, msg_bytes)

    def found_value(self, key, value, rpc_id, sock, server_node_id, target_node_address):
        payload = packet.FoundValue(key, value, self.node_id, server_node_id, rpc_id)
        msg_obj = packet.Message("found_value", payload)
        msg_bytes = pickle.dumps(msg_obj)
        self.client.found_value(sock, target_node_address, msg_bytes)

    def store(self, key, value, sock, server_node_id, target_node_address):
        payload = packet.Store(key, value, self.node_id, server_node_id)
        msg_obj = packet.Message("store", payload)
        msg_bytes = pickle.dumps(msg_obj)
        self.client.store(sock, target_node_address, msg_bytes)

    def iterative_find_nodes(self, key, seed_node=None):
        """
        找到距离目标节点最近的K个节点
        :param server_node_id:
        :param seed_nodes:
        :return:
        """
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
        for seed_node in seed_nodes:
            # 握手
            self.sendversion(seed_node,
                             Version(1, int(time.time()), self.node_id, seed_node.node_id,
                                     db.get_block_height(self.blockchain.get_wallet_address())))

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

    def hearbeat(self, node, bucket, node_idx):
        # buckets在15分钟内节点未改变过需要进行refresh操作（对buckets中的每个节点发起find node操作）
        # 如果所有节点都有返回响应，则该buckets不需要经常更新
        # 如果有节点没有返回响应，则该buckets需要定期更新保证buckets的完整性
        node_id = node.node_id
        ip = node.ip
        port = node.port

        tm = int(time.time())
        if tm - int(self.alive_nodes[node_id]) > 1800:
            # 节点的更新时间超过1min，认为已下线，移除该节点
            bucket.pop(node_idx)
            self.alive_nodes.pop(node_id)

        # print '[Info] heartbeat....'
        self.ping(self.server.socket, node_id, (ip, port))

    def minner(self):
        while True:
            # blockchain多个线程共享使用，需要加锁
            time.sleep(10)

            try:
                with self.lock:
                    new_block = self.blockchain.do_mine()
                # 广播区块
                # TODO 检测包大小，太大会导致发送失败
                self.sendblock(new_block)
            except Error as e:
                pass

            self.blockchain.set_consensus_chain()  # pow机制保证最长辆（nonce之和最大的链）

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

    def sendtx(self, tx):
        """
        广播一個交易
        :param tx:
        :return:
        """
        data_key = self.__hash_function(tx.txid)
        k_nearest_ndoes = self.iterative_find_nodes(data_key)
        if not k_nearest_ndoes:
            self.data[data_key] = tx
        for node in k_nearest_ndoes:
            tx.from_id = self.node_id
            msg_obj = packet.Message("sendtx", tx)
            msg_bytes = pickle.dumps(msg_obj)
            self.client.sendtx(self.server.socket, (node.ip, node.port), msg_bytes)

    def sendblock(self, block):
        """
        广播一个block
        :param block:
        :return:
        """
        data_key = self.__hash_function(block.current_hash)
        k_nearest_ndoes = self.iterative_find_nodes(data_key)
        if not k_nearest_ndoes:
            self.data[data_key] = block
        for node in k_nearest_ndoes:
            block.from_id = self.node_id
            msg_obj = packet.Message("sendblock", block)
            msg_bytes = pickle.dumps(msg_obj)
            print '[Info] send block', node.ip, node.port, block.current_hash
            self.client.sendblock(self.server.socket, (node.ip, node.port), msg_bytes)

    def sendversion(self, node, version):
        msg_obj = packet.Message("version", version)
        msg_bytes = pickle.dumps(msg_obj)
        self.client.sendversion(self.server.socket, (node.ip, node.port), msg_bytes)

    def sendverck(self, node, verack):
        msg_obj = packet.Message("verack", verack)
        msg_bytes = pickle.dumps(msg_obj)
        self.client.sendverack(self.server.socket, (node.ip, node.port), msg_bytes)

    # def sendmessages(self):
    #     while True:
    #         for bucket in self.buckets.buckets:
    #             for i in range(len(bucket)):
    #                 node = bucket[i]
    #                 # 要先完成握手才可以进行其他操作
    #                 if node.version == None:
    #                     continue
    #
    #                     # hearbeat
    #                     # self.hearbeat(node, bucket, i)
    #
    #                     # 发送addr消息，告诉对方节点自己所拥有的节点信息
    #                     # TODO
    #
    #                     # 发送getaddr消息，获取尽量多的节点
    #                     # TODO
    #
    #                     # 发送inv消息，请求一个区块哈希的列表
    #                     # TODO
    #
    #                     # 发送getdata消息，用于请求某个块或交易的完整信息
    #                     # TODO
    #
    #         time.sleep(10)
