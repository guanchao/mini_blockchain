# coding:utf-8
from p2p.node import NodeManager, Node
import time

client_node = NodeManager('localhost')
client_node.bootstrap([Node("localhost", 52556, 196673591351741026896772690191245219040)])

# client_node.set_data('name', 'guanchao')
print '[Info] find value',client_node.get_data('name')

# client_node.ping(client_node.server.socket, 98185628152400709107016382791375620591, ('localhost', 58421))

time.sleep(100)
# client_node.server.serve_forever()

