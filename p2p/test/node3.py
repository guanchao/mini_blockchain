# coding:utf-8
import time

from p2p.node import NodeManager, Node
from transaction import *

node = NodeManager("localhost", 3333)
node.ping(node.server.socket, 144861665166259743440473887133821631928, ('localhost', 1111))
time.sleep(10)

tx = Transaction([TxInput(None, -1, "Reward to 123123", None)], [TxOutput(20, "654321")], time.time())
node.sendtx(tx)

while True:
    pass
