# -*- coding: utf-8 -*-
"""
app/tests/test_aes.py

Проверка реализации стандартного AES с использованием официальных
тестовых векторов NIST FIPS-197 (Appendix B/C), а также базовых
самопроверок отдельных компонентов (SubBytes/InvSubBytes, ShiftRows/
InvShiftRows, MixColumns/InvMixColumns, Key Expansion).
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.crypto.aes import (
    AESCipher, encrypt_block, decrypt_block,
    sub_bytes, inv_sub_bytes, shift_rows, inv_shift_rows,
    mix_columns, inv_mix_columns, bytes_to_state, state_to_bytes,
)
from app.crypto.aes_sbox import AES_SBOX, AES_INV_SBOX
from app.crypto.aes_key_expansion import key_expansion


class TestAESOfficialVectors(unittest.TestCase):
    """FIPS-197 Appendix C test vectors."""

    PLAINTEXT = bytes.fromhex("00112233445566778899aabbccddeeff")[:16]

    def test_aes128(self):
        key = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
        expected_ct = bytes.fromhex("69c4e0d86a7b0430d8cdb78070b4c55a")
        cipher = AESCipher(key, 128)
        ct_blocks, _ = cipher.encrypt_blocks([self.PLAINTEXT])
        self.assertEqual(ct_blocks[0], expected_ct)
        pt_blocks, _ = cipher.decrypt_blocks(ct_blocks)
        self.assertEqual(pt_blocks[0], self.PLAINTEXT)

    def test_aes192(self):
        key = bytes.fromhex("000102030405060708090a0b0c0d0e0f1011121314151617")
        expected_ct = bytes.fromhex("dda97ca4864cdfe06eaf70a0ec0d7191")
        cipher = AESCipher(key, 192)
        ct_blocks, _ = cipher.encrypt_blocks([self.PLAINTEXT])
        self.assertEqual(ct_blocks[0], expected_ct)
        pt_blocks, _ = cipher.decrypt_blocks(ct_blocks)
        self.assertEqual(pt_blocks[0], self.PLAINTEXT)

    def test_aes256(self):
        key = bytes.fromhex("000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f")
        expected_ct = bytes.fromhex("8ea2b7ca516745bfeafc49904b496089")
        cipher = AESCipher(key, 256)
        ct_blocks, _ = cipher.encrypt_blocks([self.PLAINTEXT])
        self.assertEqual(ct_blocks[0], expected_ct)
        pt_blocks, _ = cipher.decrypt_blocks(ct_blocks)
        self.assertEqual(pt_blocks[0], self.PLAINTEXT)


class TestAESComponents(unittest.TestCase):
    def test_sbox_inverse_is_bijective(self):
        for i in range(256):
            self.assertEqual(AES_INV_SBOX[AES_SBOX[i]], i)

    def test_subbytes_roundtrip(self):
        state = bytes_to_state(bytes(range(16)))
        s1 = sub_bytes(state)
        s2 = inv_sub_bytes(s1)
        self.assertEqual(state, s2)

    def test_shiftrows_roundtrip(self):
        state = bytes_to_state(bytes(range(16)))
        s1 = shift_rows(state)
        s2 = inv_shift_rows(s1)
        self.assertEqual(state, s2)

    def test_mixcolumns_roundtrip(self):
        state = bytes_to_state(bytes(range(16)))
        s1 = mix_columns(state)
        s2 = inv_mix_columns(s1)
        self.assertEqual(state, s2)

    def test_key_expansion_word_count_128(self):
        key = bytes(16)
        result = key_expansion(key, nk=4, nr=10)
        self.assertEqual(len(result["words"]), 44)
        self.assertEqual(len(result["round_keys"]), 11)

    def test_key_expansion_word_count_192(self):
        key = bytes(24)
        result = key_expansion(key, nk=6, nr=12)
        self.assertEqual(len(result["words"]), 52)
        self.assertEqual(len(result["round_keys"]), 13)

    def test_key_expansion_word_count_256(self):
        key = bytes(32)
        result = key_expansion(key, nk=8, nr=14)
        self.assertEqual(len(result["words"]), 60)
        self.assertEqual(len(result["round_keys"]), 15)


class TestUnicodeRoundtrip(unittest.TestCase):
    def _roundtrip(self, text, key_bits=128):
        from app.crypto.encoding import text_to_bytes, bytes_to_text
        from app.crypto.padding import pad_zero_bytes, unpad_zero_bytes, split_into_blocks
        import os
        data = text_to_bytes(text)
        padded, info = pad_zero_bytes(data, 16)
        key = os.urandom(key_bits // 8)
        cipher = AESCipher(key, key_bits)
        blocks = split_into_blocks(padded, 16)
        ct_blocks, _ = cipher.encrypt_blocks(blocks)
        pt_blocks, _ = cipher.decrypt_blocks(ct_blocks)
        recovered_padded = b"".join(pt_blocks)
        recovered = unpad_zero_bytes(recovered_padded, info["original_length_bytes"])
        self.assertEqual(bytes_to_text(recovered), text)

    def test_russian(self):
        self._roundtrip("Привет, мир! Это тестовое сообщение на русском.")

    def test_chinese(self):
        self._roundtrip("你好，世界！这是一个测试消息。")

    def test_japanese(self):
        self._roundtrip("こんにちは世界！これはテストメッセージです。")

    def test_arabic(self):
        self._roundtrip("مرحبا بالعالم! هذه رسالة اختبار.")

    def test_trailing_zero_bytes_in_data(self):
        # Проверка, что данные, заканчивающиеся нулевыми байтами, не
        # повреждаются при удалении padding (критично важный тест!)
        from app.crypto.encoding import text_to_bytes
        from app.crypto.padding import pad_zero_bytes, unpad_zero_bytes, split_into_blocks
        import os
        data = b"Hello\x00\x00\x00"  # реальные данные сами оканчиваются нулями
        padded, info = pad_zero_bytes(data, 16)
        key = os.urandom(16)
        cipher = AESCipher(key, 128)
        blocks = split_into_blocks(padded, 16)
        ct_blocks, _ = cipher.encrypt_blocks(blocks)
        pt_blocks, _ = cipher.decrypt_blocks(ct_blocks)
        recovered_padded = b"".join(pt_blocks)
        recovered = unpad_zero_bytes(recovered_padded, info["original_length_bytes"])
        self.assertEqual(recovered, data)  # не должно потерять хвостовые нули!


class TestExperimentalCipher(unittest.TestCase):
    def test_experimental_roundtrip_various_sizes(self):
        from app.crypto.experimental_cipher import ExperimentalCipher, LINEAR_TRANSFORMS
        from app.crypto.aes_sbox import generate_sbox_standard_construction
        import os

        sbox, _ = generate_sbox_standard_construction(seed=42)
        for block_bits in (64, 128, 192, 256):
            for key_bits in (64, 128, 256):
                for transform in LINEAR_TRANSFORMS:
                    key = os.urandom(key_bits // 8)
                    cipher = ExperimentalCipher(key, block_bits, key_bits, num_rounds=10,
                                                 sbox=sbox, linear_transform=transform)
                    block = os.urandom(block_bits // 8)
                    ct, _ = cipher.encrypt_block(block)
                    pt, _ = cipher.decrypt_block(ct)
                    self.assertEqual(pt, block,
                                      f"Roundtrip failed: block={block_bits} key={key_bits} "
                                      f"transform={transform}")


class TestSboxGeneration(unittest.TestCase):
    def test_generated_sbox_is_bijective(self):
        from app.crypto.aes_sbox import generate_sbox_standard_construction, build_inverse_sbox
        for seed in range(5):
            sbox, meta = generate_sbox_standard_construction(seed=seed)
            self.assertEqual(len(set(sbox)), 256)
            inv = build_inverse_sbox(sbox)
            for i in range(256):
                self.assertEqual(inv[sbox[i]], i)

    def test_sbox_from_meta_reproducible(self):
        from app.crypto.aes_sbox import generate_sbox_standard_construction, generate_sbox_from_meta
        sbox, meta = generate_sbox_standard_construction(seed=123)
        sbox2 = generate_sbox_from_meta(meta)
        self.assertEqual(sbox, sbox2)


class TestContainerFormat(unittest.TestCase):
    def test_build_and_parse(self):
        from app.crypto.container import build_container, parse_container
        from app.crypto.aes_sbox import AES_SBOX
        s = build_container(mode="AES", cipher_mode="ECB", block_bits=128, key_bits=128,
                             rounds=10, sbox=AES_SBOX, sbox_meta={}, linear_transform="",
                             iv_hex="", original_length_bytes=11,
                             ciphertext_hex="00" * 16)
        payload = parse_container(s)
        self.assertEqual(payload["mode"], "AES")
        self.assertEqual(payload["original_length_bytes"], 11)


class TestFeistel(unittest.TestCase):
    def test_round_roundtrip(self):
        from app.crypto.feistel import feistel_round, feistel_inverse_round, generate_round_keys
        L, R = b"\x01\x02\x03\x04", b"\x05\x06\x07\x08"
        rk = generate_round_keys(b"key", 1, 4)[0]
        newL, newR, _ = feistel_round(L, R, rk)
        recL, recR, _ = feistel_inverse_round(newL, newR, rk)
        self.assertEqual((recL, recR), (L, R))

    def test_block_roundtrip_various_rounds(self):
        from app.crypto.feistel import (feistel_encrypt_block, feistel_decrypt_block,
                                         generate_round_keys)
        import os
        for num_rounds in (1, 4, 8, 16):
            rks = generate_round_keys(b"my secret key", num_rounds, 4)
            block = os.urandom(8)
            ct, _ = feistel_encrypt_block(block, rks)
            pt, _ = feistel_decrypt_block(ct, rks)
            self.assertEqual(pt, block, f"Failed for rounds={num_rounds}")

    def test_multiblock_unicode_roundtrip(self):
        from app.crypto.feistel import feistel_encrypt, feistel_decrypt
        from app.crypto.padding import pad_zero_bytes, unpad_zero_bytes
        for text in ("Привет, Фейстель!", "你好世界", "こんにちは", "مرحبا"):
            data = text.encode("utf-8")
            padded, info = pad_zero_bytes(data, 8)
            ct_blocks, _, _ = feistel_encrypt(padded, b"secretkey", 10, 8)
            pt_blocks, _ = feistel_decrypt(ct_blocks, b"secretkey", 10, 8)
            recovered = unpad_zero_bytes(b"".join(pt_blocks), info["original_length_bytes"])
            self.assertEqual(recovered.decode("utf-8"), text)

    def test_container_roundtrip(self):
        from app.crypto.feistel import build_feistel_container, parse_feistel_container
        s = build_feistel_container("00112233", 4, 8, 8)
        payload = parse_feistel_container(s)
        self.assertEqual(payload["algorithm"], "Feistel")
        self.assertEqual(payload["rounds"], 8)


if __name__ == "__main__":
    unittest.main(verbosity=2)
