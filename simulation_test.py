# coding:utf-8
import json
import random
import time
import urllib2


def bootstrap(address, seeds):
    data = {
        "seeds": seeds
    }
    req = urllib2.Request("http://" + address + "/bootstrap",
                          json.dumps(data),
                          {"Content-Type": "application/json"})
    res_data = urllib2.urlopen(req)
    res = res_data.read()
    return res


def run():
    node1 = get_node_info("127.0.0.1:5000")
    node2 = get_node_info("127.0.0.1:5001")
    node3 = get_node_info("127.0.0.1:5002")

    node1_seeds = [
        {"node_id": node2["node_id"], "ip":node2["ip"], "port":node2["port"]},
        {"node_id": node3["node_id"], "ip": node3["ip"], "port": node3["port"]}
    ]
    print node1_seeds
    bootstrap("127.0.0.1:5000", node1_seeds)

    node2_seeds = [
        {"node_id": node1["node_id"], "ip": node1["ip"], "port": node1["port"]},
        {"node_id": node3["node_id"], "ip": node3["ip"], "port": node3["port"]}
    ]
    bootstrap("127.0.0.1:5001", node2_seeds)

    node3_seeds = [
        {"node_id": node2["node_id"], "ip": node2["ip"], "port": node2["port"]},
        {"node_id": node1["node_id"], "ip": node1["ip"], "port": node1["port"]}
    ]
    bootstrap("127.0.0.1:5002", node3_seeds)

    time.sleep(30)

    node1_wallet = node1["wallet"]
    node2_wallet = node2["wallet"]
    node3_wallet = node3["wallet"]
    
    while True:

        # node1 发送给node2 node3
        node1_balance = get_balance("127.0.0.1:5000", node1_wallet)
        node1_balance = node1_balance['balance']
        if node1_balance > 0:
            amount = random.randint(1, node1_balance)
            print 'send from node1 to node2 with amount:'+str(amount)
            simulate_tx("127.0.0.1:5000", node1_wallet, node2_wallet, amount)
            time.sleep(random.randint(20,30))

        node1_balance = get_balance("127.0.0.1:5000", node1_wallet)
        node1_balance = node1_balance['balance']
        if node1_balance > 0:
            amount = random.randint(1, node1_balance)
            print 'send from node1 to node3 with amount:' + str(amount)
            simulate_tx("127.0.0.1:5000", node1_wallet, node3_wallet, amount)
            time.sleep(random.randint(20,30))

        # node2 发送给node1 node3
        node2_balance = get_balance("127.0.0.1:5001", node2_wallet)
        node2_balance = node2_balance['balance']
        if node2_balance > 0:
            amount = random.randint(1, node2_balance)
            print 'send from node2 to node1 with amount:' + str(amount)
            simulate_tx("127.0.0.1:5001", node2_wallet, node1_wallet, amount)
            time.sleep(random.randint(20,30))

        node2_balance = get_balance("127.0.0.1:5001", node2_wallet)
        node2_balance = node2_balance['balance']
        if node2_balance > 0:
            amount = random.randint(1, node2_balance)
            print 'send from node2 to node3 with amount:' + str(amount)
            simulate_tx("127.0.0.1:5001", node2_wallet, node3_wallet, amount)
            time.sleep(random.randint(20,30))
        #
        # node3 发送给node1 node2
        node3_balance = get_balance("127.0.0.1:5002", node3_wallet)
        node3_balance = node3_balance['balance']
        if node3_balance > 0:
            amount = random.randint(1, node3_balance)
            print 'send from node3 to node1 with amount:' + str(amount)
            simulate_tx("127.0.0.1:5002", node3_wallet, node1_wallet, amount)
            time.sleep(random.randint(20,30))

        node3_balance = get_balance("127.0.0.1:5002", node3_wallet)
        node3_balance = node3_balance['balance']
        if node3_balance > 0:
            amount = random.randint(1, node3_balance)
            print 'send from node3 to node2 with amount:' + str(amount)
            simulate_tx("127.0.0.1:5002", node3_wallet, node2_wallet, amount)
            time.sleep(random.randint(20,30))

        time.sleep(10)


def simulate_tx(address, sender, receiver, amount):
    data = {
        "sender": sender,
        "receiver": receiver,
        "amount": amount
    }

    req = urllib2.Request(url="http://" + address + "/transactions/new",
                          headers={"Content-Type": "application/json"}, data=json.dumps(data))
    res_data = urllib2.urlopen(req)
    res = res_data.read()
    return res


def get_balance(address, wallet_addres):
    req = urllib2.Request(url="http://" + address + "/balance?address=" + wallet_addres,
                          headers={"Content-Type": "application/json"})

    res_data = urllib2.urlopen(req)
    res = res_data.read()
    return json.loads(res)


def get_node_info(address):
    req = urllib2.Request(url="http://" + address + "/curr_node",
                          headers={"Content-Type": "application/json"})

    res_data = urllib2.urlopen(req)
    res = res_data.read()
    return json.loads(res)


run()
