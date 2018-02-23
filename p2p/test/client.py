# coding:utf-8
from p2p.node import NodeManager, Node
import time

client_node = NodeManager('localhost')
client_node.bootstrap([Node("localhost", 56715, 281201721094562312409295267246465998470)])

client_node.ping(client_node.server.socket, 50401779254185384080320426017077202973, ('localhost', 58837))

time.sleep(100)
# client_node.server.serve_forever()

