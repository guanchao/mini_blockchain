# coding:utf-8
from p2p.node import NodeManager, Node
import time

client_node = NodeManager('localhost', 5555)


client_node.ping(client_node.server.socket, 117867121185419901996991408112393888325, ('localhost', 1111))

time.sleep(4)
client_node.set_data('name', 'guanchao')
print '[Info] find value',client_node.get_data('name')

client_node.store('name', 'guanchao', client_node.server.socket, 117867121185419901996991408112393888325, ('localhost', 1111))

time.sleep(4)


print client_node.data
time.sleep(100)
# client_node.server.serve_forever()


