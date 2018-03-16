# coding:utf-8
import hashlib

import rsa


def get_address(pubkey):
    """
    简化钱包地址的生成
    :return:
    """
    sha = hashlib.sha256(pubkey.__str__())
    return sha.hexdigest()

def sign(privkey, data):
    return rsa.sign(data.encode(), privkey, 'SHA-256')


def verify(data, signature, pubkey):
    return rsa.verify(data.encode(), signature, pubkey)

class Wallet(object):
    """
    简化钱包，一个钱包只包含一个密钥对（公钥+私钥）
    """

    def __init__(self):
        pubkey, privkey = rsa.newkeys(1024)

        self.pubkey = pubkey
        self.privkey = privkey

    def get_address(self):
        """
        简化钱包地址的生成
        :return:
        """
        sha = hashlib.sha256(self.pubkey.__str__())
        return sha.hexdigest()


