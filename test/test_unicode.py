# -*- coding: utf-8 -*-

import sys
import unittest

from vt102 import *

if sys.version_info[0] > 2:
    class TestUnicode(unittest.TestCase):
        def test_unicode_input(self):
            s = stream()
            sc = screen((2, 4))
            sc.attach(s)

            text = u"тест"
            s.process(text)

            self.assertEqual(sc.display[0], u"тест")

if __name__ == "__main__":
    unittest.main()

