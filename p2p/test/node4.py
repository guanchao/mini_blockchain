# coding:utf-8
import time

from p2p.node import NodeManager, Node

node = NodeManager("localhost", 4444)
node.bootstrap([
    Node("localhost", 1111, 117867121185419901996991408112393888325),
    Node("localhost", 2222, 8447281794765442434822375461178311419),
    Node("localhost", 3333, 112294003589568940103854561280857049922),
])

while True:
    pass
