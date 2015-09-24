import unittest

from vt102 import *

class TestUnknown(unittest.TestCase):
    def test_process_fails_on_unknown_escape_by_default(self):
        command = "\x1b\x99"

        s = stream()
        with self.assertRaises(StreamProcessError):
            s.process(command)

    def test_process_doesnt_fail_on_unknown_escape_when_set_to_false(self):
        command = "\x1b\x99"

        s = stream(fail_on_unknown_esc=False)
        s.process(command)

if __name__ == "__main__":
    unittest.main()
