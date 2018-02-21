# coding:utf-8
from p2p.node import NodeManager

node = NodeManager("localhost", 3001, 1111)

node.server.serve_forever()