import os
import sys
sys.path.insert(0, os.path.realpath(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))))

import unittest
import pycode_similar

class TestCases(unittest.TestCase):

    def test_basic_detect(self):
        s1 = """
def foo(a):
    if a > 1:
        return True
    return False
        """
        s2 = """
class A(object):
    def __init__(self, a):
        self._a = a
        
    def bar(self):
        if self._a > 2:
            return True
        return False
        """
        result = pycode_similar.detect([s1, s2])
        self.assertGreater(result[0][1][0].plagiarism_percent, 0.5)

    def test_name(self):
            s1 = """
def foo(a):
    if a > 1:
        return True
    return False
            """
            s2 = """
def bar(b):
    if b > 1:
        return True
    return False
            """
            result = pycode_similar.detect([s1, s2])
            self.assertEqual(result[0][1][0].plagiarism_percent, 1)

    def test_equal(self):
            s1 = """
def foo(a):
    if a == 1:
        return True
    return False
            """
            s2 = """
def bar(b):
    if 1 == b:
        return True
    return False
            """
            result = pycode_similar.detect([s1, s2])
            self.assertEqual(result[0][1][0].plagiarism_percent, 1)

    def test_gt_lt(self):
            s1 = """
def foo(a):
    if a > 1:
        return True
    return False
            """
            s2 = """
def bar(b):
    if 1 < b:
        return True
    return False
            """
            result = pycode_similar.detect([s1, s2])
            self.assertEqual(result[0][1][0].plagiarism_percent, 1)

    def test_gte_lte(self):
            s1 = """
def foo(a):
    if a >= 1:
        return True
    return False
            """
            s2 = """
def bar(b):
    if 1 <= b:
        return True
    return False
            """
            result = pycode_similar.detect([s1, s2])
            self.assertEqual(result[0][1][0].plagiarism_percent, 1)


if __name__ == "__main__":
#     import sys;sys.argv = ['', 'Test.test_reload_custom_code_after_changes_in_class']
    unittest.main()

