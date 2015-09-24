import unittest

from vt102 import *
from vt102.control import *

class TestUnicode(unittest.TestCase):
    def test_unicode_input(self):
        s = stream()
        sc = screen((2, 4))
        sc.attach(s)

        s.process(u"тест")

        self.assertEqual(sc.display[0], u"тест")

if __name__ == "__main__":
    unittest.main()

