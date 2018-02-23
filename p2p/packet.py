import json

MSG_TYPE_PING = 101
MSG_TYPE_PONG = 102

MSG_TYPE_FIND_NEIGHBORS = 103
MSG_TYPE_FOUND_NEIGHBORS = 104

MSG_TYPE_FIND_VALUE = 105
MSG_TYPE_FOUND_VALUE = 106

MSG_TYPE_STORE = 107

class Ping(object):
    def __init__(self, from_id, to_id):
        self.msg_type = MSG_TYPE_PING
        self.from_id = from_id
        self.to_id = to_id

    def __str__(self):
        return json.dumps(self.__dict__)


class Pong(object):
    def __init__(self, from_id, to_id):
        self.msg_type = MSG_TYPE_PONG
        self.from_id = from_id
        self.to_id = to_id

    def __str__(self):
        return json.dumps(self.__dict__)


class FindNeighbors(object):
    def __init__(self, target_id, from_id, to_id, rpc_id):
        self.msg_type = MSG_TYPE_FIND_NEIGHBORS
        self.target_id = target_id
        self.from_id = from_id
        self.to_id = to_id
        self.rpc_id = rpc_id

    def __str__(self):
        return json.dumps(self.__dict__)


class FoundNeighbors(object):
    def __init__(self, target_id, from_id, to_id, rpc_id, neighbors):
        self.msg_type = MSG_TYPE_FOUND_NEIGHBORS
        self.target_id = target_id
        self.from_id = from_id
        self.to_id = to_id
        self.rpc_id = rpc_id
        self.neighbors = neighbors

    def __str__(self):
        return json.dumps(self.__dict__)


class FindValue(object):
    def __init__(self, key, from_id, to_id, rpc_id):
        self.msg_type = MSG_TYPE_FIND_VALUE
        self.key = key
        self.from_id = from_id
        self.to_id = to_id
        self.rpc_id = rpc_id

    def __str__(self):
        return json.dumps(self.__dict__)


class FoundValue(object):
    def __init__(self, key, value, from_id, to_id, rpc_id):
        self.msg_type = MSG_TYPE_FOUND_VALUE
        self.key = key
        self.value = value
        self.from_id = from_id
        self.to_id = to_id
        self.rpc_id = rpc_id

    def __str__(self):
        return json.dumps(self.__dict__)


class Store(object):
    def __init__(self, key, value, from_id, to_id):
        self.msg_type = MSG_TYPE_STORE
        self.key = key
        self.value = value
        self.from_id = from_id
        self.to_id = to_id

    def __str__(self):
        return json.dumps(self.__dict__)

