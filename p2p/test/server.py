# coding:utf-8
import time

from p2p.node import NodeManager, Node

node = NodeManager("localhost")
node.bootstrap([Node("localhost", 58837, 50401779254185384080320426017077202973), Node("localhost", 58839, 193163848851503275379094855662998178321)])

time.sleep(600)