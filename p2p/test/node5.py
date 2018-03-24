# coding:utf-8
from p2p.node import NodeManager, Node
import time

client_node = NodeManager('localhost', 5555)


client_node.ping(client_node.server.socket, 93768923979724802864281382409093076857, ('localhost', 1111))

time.sleep(4)
# client_node.set_data('name', 'guanchao')
# print '[Info] find value',client_node.get_data('name')

client_node.store('name', 'guanchao', client_node.server.socket, 93768923979724802864281382409093076857, ('localhost', 1111))

time.sleep(4)
print '[Info] find value',client_node.get_data('name')

time.sleep(4)
print '[Info] find value',client_node.get_data('aaa')

print client_node.data
time.sleep(100)
# client_node.server.serve_forever()


