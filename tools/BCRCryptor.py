import binascii
import random
from typing import Dict
import msgpack
from Crypto.Cipher import AES
import base64


class BCRCryptor:
    @staticmethod
    def msgpack_pack(data: object):
        return msgpack.packb(data, use_bin_type=False)

    @staticmethod
    def msgpack_unpack(packed: bytes):
        return msgpack.unpackb(packed, strict_map_key=False)

    @staticmethod
    def text_pad(packed: bytes) -> bytes:
        padding_size = 0x10-(len(packed) % 0x10)
        return packed+bytes([padding_size])*padding_size

    @staticmethod
    def text_unpad(padded: bytes) -> bytes:
        padding_size = padded[-1]
        return padded[:-padding_size]

    @staticmethod
    def aes_encrypt(padded: bytes, key: bytes) -> bytes:
        cryptor = AES.new(key, AES.MODE_CBC, b'ha4nBYA2APUD6Uv1')
        return cryptor.encrypt(padded)

    @staticmethod
    def aes_decrypt(encrypted: bytes, key: bytes) -> bytes:
        cryptor = AES.new(key, AES.MODE_CBC, b'ha4nBYA2APUD6Uv1')
        return cryptor.decrypt(encrypted)

    @staticmethod
    def squeeze(encrypted: bytes, key: bytes):
        return encrypted+key

    @staticmethod
    def split(raw: bytes):
        return raw[:-32], raw[-32:]

    def decrypt(self, raw: bytes) -> Dict:
        try:
            raw = base64.b64decode(raw, validate=True)
        except binascii.Error:
            raw = raw
        encrypted, key = self.split(raw)
        padded = self.aes_decrypt(encrypted, key)
        packed = self.text_unpad(padded)
        data = self.msgpack_unpack(packed)
        return data

    def encrypt(self, data: object, key: bytes)->bytes:
        packed = self.msgpack_pack(data)
        padded = self.text_pad(packed)
        encrypted = self.aes_encrypt(padded, key)
        raw = self.squeeze(encrypted, key)
        return raw

    def get_key(self, raw: bytes)->bytes:
        try:
            raw = base64.b64decode(raw, validate=True)
        except binascii.Error:
            raw = raw
        return self.split(raw)[-1]

    @staticmethod
    def gen_aes_key() -> bytes:
        rand_hex = bytes([random.choice(b'0123456789abcdef')
                         for _ in range(32)])
        return base64.b64encode(rand_hex)[:32]
