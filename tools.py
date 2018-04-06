# coding:utf-8
import rsa


def create_genisus_keypair():
    # 第一个节点的密钥对
    pubkey, privkey = rsa.newkeys(1024)
    with open('genisus_public.pem', 'w+') as f:
        f.write(pubkey.save_pkcs1().decode())

    with open('genisus_private.pem', 'w+') as f:
        f.write(privkey.save_pkcs1().decode())

# create_genisus_keypair()
