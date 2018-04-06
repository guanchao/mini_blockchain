# coding=utf-8
import json


class Message(object):
    def __init__(self, command, payload):
        """
        :param command: <str> 命令
        :param payload: <byte[]> 每个command对应的payload不一样
        """
        self.command = command
        self.payload = payload


class Version(object):
    def __init__(self, version, timestamp, from_id, to_id, best_height):
        self.version = version
        self.timestamp = timestamp
        self.from_id = from_id
        self.to_id = to_id
        self.best_height = best_height


class Verack(object):
    def __init__(self, version, timestamp, from_id, to_id, best_height):
        self.version = version
        self.timestamp = timestamp
        self.from_id = from_id
        self.to_id = to_id
        self.best_height = best_height


class Ping(object):
    def __init__(self, from_id, to_id):
        self.from_id = from_id
        self.to_id = to_id

    def __str__(self):
        return json.dumps(self.__dict__)


class Pong(object):
    def __init__(self, from_id, to_id):
        self.from_id = from_id
        self.to_id = to_id

    def __str__(self):
        return json.dumps(self.__dict__)


class FindNeighbors(object):
    def __init__(self, target_id, from_id, to_id, rpc_id):
        self.target_id = target_id
        self.from_id = from_id
        self.to_id = to_id
        self.rpc_id = rpc_id

    def __str__(self):
        return json.dumps(self.__dict__)


class FoundNeighbors(object):
    def __init__(self, target_id, from_id, to_id, rpc_id, neighbors):
        self.target_id = target_id
        self.from_id = from_id
        self.to_id = to_id
        self.rpc_id = rpc_id
        self.neighbors = neighbors

    def __str__(self):
        return json.dumps(self.__dict__)


class FindValue(object):
    def __init__(self, key, from_id, to_id, rpc_id):
        self.key = key
        self.from_id = from_id
        self.to_id = to_id
        self.rpc_id = rpc_id

    def __str__(self):
        return json.dumps(self.__dict__)


class FoundValue(object):
    def __init__(self, key, value, from_id, to_id, rpc_id):
        self.key = key
        self.value = value
        self.from_id = from_id
        self.to_id = to_id
        self.rpc_id = rpc_id

    def __str__(self):
        return json.dumps(self.__dict__)


class Store(object):
    def __init__(self, key, value, from_id, to_id):
        self.key = key
        self.value = value
        self.from_id = from_id
        self.to_id = to_id

    def __str__(self):
        return json.dumps(self.__dict__)
