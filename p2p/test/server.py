# coding:utf-8
import time

from p2p.node import NodeManager, Node

# node1 = NodeManager("localhost", 1111)
# node2 = NodeManager("localhost", 2222)
node4 = NodeManager('localhost', 4444)
node4.bootstrap([Node("localhost", 1111, 111138798567493407761578227511392983486), Node("localhost", 2222, 99148516122896888249025030606800545437)])

time.sleep(600)