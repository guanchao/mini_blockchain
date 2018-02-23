# coding:utf-8
from p2p.node import NodeManager, Node
import time

client_node = NodeManager('localhost', 9999)
client_node.bootstrap([Node("localhost", 4444, 141256802709927127991837196672120538555)])

client_node.ping(client_node.server.socket, 111138798567493407761578227511392983486, ('localhost', 1111))
#
time.sleep(100)
# client_node.server.serve_forever()

