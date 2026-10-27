import unittest
from app.crypto.sbox import generate_sbox
from app.crypto.aes_sbox import AES_SBOX
from app.crypto.feistel import pad_both_sides, F, encrypt, decrypt, rotate_right


class TestEducationalFeistel(unittest.TestCase):
    def test_local_sbox_is_algorithmic_aes_sbox(self):
        self.assertEqual(generate_sbox(), AES_SBOX)

    def test_padding_both_sides(self):
        value, info = pad_both_sides("1011", 8)
        self.assertEqual(value, "00101100")
        self.assertEqual((info["left"], info["right"]), (2, 2))

    def test_rotate_right_one_bit(self):
        self.assertEqual(rotate_right("10110010", 1), "01011001")

    def test_f_has_required_three_steps(self):
        data = F("10110110", "01101001", generate_sbox())
        self.assertEqual(data["xor"], "11011111")
        self.assertEqual(data["result"], rotate_right(data["sbox"], 1))
        self.assertEqual(len(data["sbox_lookups"]), 1)

    def test_encrypt_decrypt_roundtrip(self):
        enc = encrypt("1011011011001010", "01101001", 4, generate_sbox())
        dec = decrypt(enc["result"], "01101001", 4, generate_sbox())
        self.assertEqual(dec["result"], enc["block_padding"]["after"])


if __name__ == "__main__":
    unittest.main()
