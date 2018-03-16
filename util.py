# coding:utf-8
import hashlib


def calculate_hash(index, previous_hash, timestamp, merkleroot, nonce, difficulty):
    value = str(index) + str(previous_hash) + str(timestamp) + str(merkleroot) + str(nonce) + str(difficulty)
    sha = hashlib.sha256(value.encode('utf-8'))
    return str(sha.hexdigest())


def calculate_block_hash(block):
    return calculate_hash(index=block.index,
                          previous_hash=block.previous_hash,
                          timestamp=block.timestamp,
                          merkleroot=block.merkleroot,
                          nonce=block.nonce,
                          difficulty=block.difficulty)


def check_block(block):
    """
    校验区块
    :param block:
    :return:
    """
    cal_hash = calculate_hash(index=block.index,
                              previous_hash=block.previous_hash,
                              timestamp=block.timestamp,
                              merkleroot=block.merkleroot,
                              nonce=block.nonce,
                              difficulty=block.difficulty)

    if (cal_hash[0:block.difficulty] == '0' * block.difficulty) \
            and (block.current_hash == calculate_block_hash(block)):
        return True
    else:
        return False


def get_hash(data):
    sha = hashlib.sha256(data)
    return sha.hexdigest()
