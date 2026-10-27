# -*- coding: utf-8 -*-
import hashlib
import unittest

from app.crypto.hash_visual import trace_hash, SHA256_IV, MD5_IV


class TestHashVisualizer(unittest.TestCase):
    def test_sha256_trace_matches_hashlib(self):
        for text in ('', 'abc', 'Привет, мир!', 'a' * 1000):
            result = trace_hash(text, 'sha256')
            self.assertEqual(result['digest'], hashlib.sha256(text.encode('utf-8')).hexdigest())
            self.assertEqual(result['iv'], SHA256_IV)
            self.assertEqual(len(result['blocks'][0]['rounds']), 64)

    def test_md5_trace_matches_hashlib(self):
        for text in ('', 'abc', 'Привет, мир!', 'a' * 1000):
            result = trace_hash(text, 'md5')
            self.assertEqual(result['digest'], hashlib.md5(text.encode('utf-8')).hexdigest())
            self.assertEqual(result['iv'], MD5_IV)
            self.assertEqual(len(result['blocks'][0]['rounds']), 64)


if __name__ == '__main__':
    unittest.main()
