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

    def test_space_and_comments(self):
        s1 = """
def foo(a):
    \"""
    foo comments.
    \"""
    if a >= 1:
        return True
        
    # this should return False    
    return False
            """
        s2 = """
def bar(b):
# bar comments.
    if 1 <= b:
        \"""
        This should
        return True
        \"""
        return True
    return False
            """
        result = pycode_similar.detect([s1, s2])
        self.assertEqual(result[0][1][0].plagiarism_percent, 1)

    def test_expr(self):
        s1 = """
def foo(a):
    yield c
            """
        s2 = """
def bar(b):
    yield a
            """
        result = pycode_similar.detect([s1, s2])
        self.assertEqual(result[0][1][0].plagiarism_percent, 1)

    def test_no_function(self):
        s1 = """
def foo(a):
    c = a
            """
        s2 = """
class B(object):
    pass
            """
        try:
            result = pycode_similar.detect([s2, s1])
        except Exception as ex:
            self.assertEqual(ex.source, 0)
        result = pycode_similar.detect([s1, s2])
        self.assertEqual(result[0][1][0].plagiarism_percent, 0)

    def test_strip_print(self):
        s1 = """
def foo(a):
    a = b
    print('abc', a)
            """
        s2 = """
def foo(a):
    print('abc', bar())
    a = b
            """

        result = pycode_similar.detect([s1, s2])
        self.assertEqual(result[0][1][0].plagiarism_percent, 1)

    def test_strip_import(self):
        s1 = """
def foo():
    import sys
    from os import path
            """
        s2 = """
def foo():
    import os
    import ast
    from collections import Counter
            """

        result = pycode_similar.detect([s1, s2])
        self.assertEqual(result[0][1][0].plagiarism_percent, 1)

    def test_module_level(self):
        s1 = """
def main():
    s = 0
    for j in range(10):
        for i in range(10):
            if i > j:
                s += i + j
    print(s)

if __name__ == '__main__':
    main()
"""
        s2 = """
s = 0
for j in range(10):
    for i in range(10):
        if i > j:
            s += i + j
print(s)
"""
        result = pycode_similar.detect([s1, s2], module_level=True)
        sum_plagiarism_percent, *tail = pycode_similar.summarize(result[0][1])
        # s1.main vs s2.__main__ AND s1.__main__ vs s2.__main__
        self.assertGreater(sum_plagiarism_percent, 0.6)

        result = pycode_similar.detect([s2, s1], module_level=True)
        sum_plagiarism_percent, *tail = pycode_similar.summarize(result[0][1])
        # s2.__main__ vs s1.main
        self.assertGreater(sum_plagiarism_percent, 0.85)

    def test_keep_prints(self):
        s1 = """
a = []
for j in range(10):
    for i in range(10):
        a.append(i - j)
print(a)
print(abs(el) * el for el in a if abs(el) > 2)
"""
        s2 = """
a = [
    i - j
    for j in range(10)
    for i in range(10)
]
print(a)
print(abs(el) * el for el in a if abs(el) > 2)
"""

        result = pycode_similar.detect([s1, s2], module_level=True, keep_prints=False)
        self.assertLess(result[0][1][0].plagiarism_percent, 0.2)

        result = pycode_similar.detect([s1, s2], module_level=True, keep_prints=True)
        self.assertGreater(result[0][1][0].plagiarism_percent, 0.5)


if __name__ == "__main__":
    #     import sys;sys.argv = ['', 'Test.test_reload_custom_code_after_changes_in_class']
    unittest.main()
