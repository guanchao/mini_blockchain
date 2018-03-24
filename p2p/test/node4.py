# coding:utf-8
import time

from p2p.node import NodeManager, Node

node = NodeManager("localhost", 4444)
node.bootstrap([
    Node("localhost", 1111, 15688444429201978185935785687706502042),
    Node("localhost", 2222, 127597368099570493722252948605155977663),
    Node("localhost", 3333, 306409833593941680791903200557937784695),
])

while True:
    pass
