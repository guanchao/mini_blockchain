# coding:utf-8
import hashlib
from binascii import unhexlify, hexlify, Error

import rsa


class Wallet(object):
    """
    简化钱包，一个钱包只包含一个密钥对（公钥+私钥）
    """

    def __init__(self, genisus_node):
        if genisus_node:
            pubkey, privkey = self.get_genisus_keypair()
        else:
            pubkey, privkey = rsa.newkeys(1024)

        self.pubkey = pubkey
        self.privkey = privkey
        self.address = Wallet.get_address(self.pubkey)

    def get_genisus_keypair(self):
        with open('genisus_public.pem', 'r') as f:
            pubkey = rsa.PublicKey.load_pkcs1(f.read().encode())

        with open('genisus_private.pem', 'r') as f:
            privkey = rsa.PrivateKey.load_pkcs1(f.read().encode())

        return pubkey, privkey

    @staticmethod
    def get_address(pubkey):
        """
        钱包地址
        :param pubkey: <PublicKey>对象，公钥
        :return:
        """
        sha = hashlib.sha256(str(pubkey))
        hash_256_value = sha.hexdigest()
        obj = hashlib.new('ripemd160', hash_256_value.encode('utf-8'))
        ripemd_160_bytes = obj.digest()
        return Wallet.b58encode(ripemd_160_bytes)

    @staticmethod
    def b58encode(b):
        """
        将bytes转换成base58字符串
        :param b: <byte数组>
        :return:
        """
        b58_digits = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
        n = int('0x0' + hexlify(b).decode('utf8'), 16)

        res = []
        while n > 0:
            n, r = divmod(n, 58)
            res.append(b58_digits[r])
        res = ''.join(res[::-1])

        import sys
        czero = b'\x00'
        if sys.version > '3':
            # In Python3 indexing a bytes returns numbers, not characters.
            czero = 0
        pad = 0
        for c in b:
            if c == czero:
                pad += 1
            else:
                break
        return b58_digits[0] * pad + res

    @staticmethod
    def b58decode(s):
        """
        将base58编码的字符串转换成bytes数组
        :param s: <str> base58编码后的字符串
        :return: <byte数组>
        """
        b58_digits = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
        if not s:
            return b''

        n = 0
        for c in s:
            n *= 58
            if c not in b58_digits:
                raise Error('Character %r is not a valid base58 character' % c)
            digit = b58_digits.index(c)
            n += digit

        h = '%x' % n
        if len(h) % 2:
            h = '0' + h
        res = unhexlify(h.encode('utf8'))

        pad = 0
        for c in s[:-1]:
            if c == b58_digits[0]:
                pad += 1
            else:
                break
        return b'\x00' * pad + res
