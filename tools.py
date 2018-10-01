# coding:utf-8
import rsa


def create_genisus_keypair():
    # 第一个节点的密钥对
    pubkey, privkey = rsa.newkeys(1024)
    with open('genisus_public.pem', 'w+') as f:
        f.write(pubkey.save_pkcs1().decode())

    with open('genisus_private.pem', 'w+') as f:
        f.write(privkey.save_pkcs1().decode())

# 导入密钥
with open('genisus_private.pem', 'r') as f:
    privkey = rsa.PrivateKey.load_pkcs1(f.read().encode())

with open('genisus_public.pem', 'r') as f:
    pubkey = rsa.PublicKey.load_pkcs1(f.read().encode())

# 明文
message = 'hello world'

# 公钥加密
crypto = rsa.encrypt(message.encode(), pubkey)

# 私钥解密
message = rsa.decrypt(crypto, privkey).decode()
print(message)


# 明文
message = 'hello world'
# 导入密钥
with open('genisus_private.pem', 'r') as f:
    privkey = rsa.PrivateKey.load_pkcs1(f.read().encode())

with open('genisus_public.pem', 'r') as f:
    pubkey = rsa.PublicKey.load_pkcs1(f.read().encode())
# 私钥签名
signature = rsa.sign(message.encode(), privkey, 'SHA-1')

# 公钥验证
try:
    rsa.verify(message.encode(), signature, pubkey)
except rsa.pkcs1.VerificationError:
    print 'invalid'