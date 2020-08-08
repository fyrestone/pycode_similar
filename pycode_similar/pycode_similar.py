# -*- coding: utf-8 -*-
__author__ = 'fyrestone@outlook.com'
__version__ = '1.4'

import sys
import ast
import difflib
import operator
import argparse
import itertools
from collections import Counter

# avoid using six to keep dependency clean
if sys.version_info >= (3, 3):
    import collections.abc as collections
else:
    import collections

if sys.version_info[0] == 3:
    string_types = str
else:
    string_types = basestring


class BaseNodeNormalizer(ast.NodeTransformer):
    """
    Clean node attributes, delete the attributes that are not helpful for recognition repetition.
    """

    def __init__(self, keep_prints=False):
        super(BaseNodeNormalizer, self).__init__()
        self.keep_prints = keep_prints
        self._node_count = 0

    @staticmethod
    def _mark_docstring_sub_nodes(node):
        """
        Inspired by ast.get_docstring, mark all docstring sub nodes.

        Case1:
        regular docstring of function/class/module

        Case2:
        def foo(self):
            '''pure string expression'''
            for x in self.contents:
                '''pure string expression'''
                print x
            if self.abc:
                '''pure string expression'''
                pass

        Case3:
        def foo(self):
            if self.abc:
                print('ok')
            else:
                '''pure string expression'''
                pass

        :param node: every ast node
        :return:
        """

        def _mark_docstring_nodes(body):
            if body and isinstance(body, collections.Sequence):
                for n in body:
                    if isinstance(n, ast.Expr) and isinstance(n.value, ast.Str):
                        n.is_docstring = True

        node_body = getattr(node, 'body', None)
        _mark_docstring_nodes(node_body)
        node_orelse = getattr(node, 'orelse', None)
        _mark_docstring_nodes(node_orelse)

    @staticmethod
    def _is_docstring(node):
        return getattr(node, 'is_docstring', False)

    def generic_visit(self, node):
        self._node_count = self._node_count + 1
        self._mark_docstring_sub_nodes(node)
        return super(BaseNodeNormalizer, self).generic_visit(node)

    def visit_Constant(self, node):
        # introduce a special value for erasing constant node value,
        # del node.value will make node.s and node.n raise Exception.
        # for Python 3.8
        dummy_value = '__pycode_similar_dummy_value__'
        if type(node) == str:
            node.value = dummy_value
        self.generic_visit(node)

    def visit_Str(self, node):
        del node.s
        self.generic_visit(node)
        return node

    def visit_Expr(self, node):
        if not self._is_docstring(node):
            self.generic_visit(node)
            if hasattr(node, 'value'):
                return node

    def visit_arg(self, node):
        """
        remove arg name & annotation for python3
        :param node: ast.arg
        :return:
        """
        del node.arg
        del node.annotation
        self.generic_visit(node)
        return node

    def visit_Name(self, node):
        del node.id
        del node.ctx
        self.generic_visit(node)
        return node

    def visit_Attribute(self, node):
        del node.attr
        del node.ctx
        self.generic_visit(node)
        return node

    def visit_Call(self, node):
        func = getattr(node, 'func', None)
        if not self.keep_prints and func and isinstance(func, ast.Name) and func.id == 'print':
            return  # remove print call and its sub nodes for python3
        self.generic_visit(node)
        return node

    def visit_Compare(self, node):

        def _simple_nomalize(*ops_type_names):
            if node.ops and len(node.ops) == 1 and type(node.ops[0]).__name__ in ops_type_names:
                if node.left and node.comparators and len(node.comparators) == 1:
                    left, right = node.left, node.comparators[0]
                    if type(left).__name__ > type(right).__name__:
                        left, right = right, left
                        node.left = left
                        node.comparators = [right]
                        return True
            return False

        if _simple_nomalize('Eq'):
            pass

        if _simple_nomalize('Gt', 'Lt'):
            node.ops = [{ast.Lt: ast.Gt, ast.Gt: ast.Lt}[type(node.ops[0])]()]

        if _simple_nomalize('GtE', 'LtE'):
            node.ops = [{ast.LtE: ast.GtE, ast.GtE: ast.LtE}[type(node.ops[0])]()]

        self.generic_visit(node)
        return node

    def visit_Print(self, node):
        if not self.keep_prints:
            # remove print stmt for python2
            return
        self.generic_visit(node)
        return node

    def visit_Import(self, node):
        # remove import ...
        pass

    def visit_ImportFrom(self, node):
        # remove from ... import ...
        pass


class ModuleNodeCollector(BaseNodeNormalizer):
    """
    Normalize and remove all class nodes and function nodes - leave only module level nodes.
    """

    def __init__(self, *args, **kwargs):
        super(ModuleNodeCollector, self).__init__(*args, **kwargs)
        self._module_node = None

    def visit_ClassDef(self, node):
        # remove class ...
        return

    def visit_FunctionDef(self, node):
        # remove function ...
        return

    def visit_Module(self, node):
        self._module_node = node
        count = self._node_count
        self.generic_visit(node)
        node.name = '__main__'
        node.lineno = 1
        node.col_offset = 0
        node.nsubnodes = self._node_count - count
        return node

    def get_module_node(self):
        return self._module_node


class FuncNodeCollector(BaseNodeNormalizer):
    """
    Normalize and collect all function nodes.
    """

    def __init__(self, *args, **kwargs):
        super(FuncNodeCollector, self).__init__(*args, **kwargs)
        self._curr_class_names = []
        self._func_nodes = []
        self._last_node_lineno = -1

    def generic_visit(self, node):
        self._last_node_lineno = max(getattr(node, 'lineno', -1), self._last_node_lineno)
        return super(FuncNodeCollector, self).generic_visit(node)

    def visit_ClassDef(self, node):
        self._curr_class_names.append(node.name)
        self.generic_visit(node)
        self._curr_class_names.pop()
        return node

    def visit_FunctionDef(self, node):
        node.name = '.'.join(itertools.chain(self._curr_class_names, [node.name]))
        self._func_nodes.append(node)
        count = self._node_count
        self.generic_visit(node)
        node.endlineno = self._last_node_lineno
        node.nsubnodes = self._node_count - count
        return node

    def get_function_nodes(self):
        return self._func_nodes


class FuncInfo(object):
    """
    Part of the astor library for Python AST manipulation.

    License: 3-clause BSD

    Copyright 2012 (c) Patrick Maupin
    Copyright 2013 (c) Berker Peksag

    """

    class NonExistent(object):
        pass

    def __init__(self, func_node, code_lines):
        assert isinstance(func_node, (ast.FunctionDef, ast.Module))
        self._func_node = func_node
        self._code_lines = code_lines
        self._func_name = func_node.__dict__.pop('name', '')
        self._func_code = None
        self._func_code_lines = None
        self._func_ast = None
        self._func_ast_lines = None

    def __str__(self):
        return '<' + type(self).__name__ + ': ' + self.func_name + '>'

    @property
    def func_name(self):
        return self._func_name

    @property
    def func_node(self):
        return self._func_node

    @property
    def func_code(self):
        if self._func_code is None:
            self._func_code = ''.join(self.func_code_lines)
        return self._func_code

    @property
    def func_code_lines(self):
        if self._func_code_lines is None:
            self._func_code_lines = self._retrieve_func_code_lines(self._func_node, self._code_lines)
        return self._func_code_lines

    @property
    def func_ast(self):
        if self._func_ast is None:
            self._func_ast = self._dump(self._func_node)
        return self._func_ast

    @property
    def func_ast_lines(self):
        if self._func_ast_lines is None:
            self._func_ast_lines = self.func_ast.splitlines(True)
        return self._func_ast_lines

    @staticmethod
    def _retrieve_func_code_lines(func_node, code_lines):
        if not isinstance(func_node, (ast.FunctionDef, ast.Module)):
            return []
        if not isinstance(code_lines, collections.Sequence) or isinstance(code_lines, string_types):
            return []
        if getattr(func_node, 'endlineno', -1) < getattr(func_node, 'lineno', 0):
            return []
        lines = code_lines[func_node.lineno - 1: func_node.endlineno]
        if lines:
            padding = lines[0][:-len(lines[0].lstrip())]
            stripped_lines = []
            for l in lines:
                if l.startswith(padding):
                    stripped_lines.append(l[len(padding):])
                else:
                    stripped_lines = []
                    break
            if stripped_lines:
                return stripped_lines
        return lines

    @staticmethod
    def _iter_node(node, name='', missing=NonExistent):
        """Iterates over an object:

           - If the object has a _fields attribute,
             it gets attributes in the order of this
             and returns name, value pairs.

           - Otherwise, if the object is a list instance,
             it returns name, value pairs for each item
             in the list, where the name is passed into
             this function (defaults to blank).

        """
        fields = getattr(node, '_fields', None)
        if fields is not None:
            for name in fields:
                value = getattr(node, name, missing)
                if value is not missing:
                    yield value, name
        elif isinstance(node, list):
            for value in node:
                yield value, name

    @staticmethod
    def _dump(node, name=None, initial_indent='', indentation='    ',
              maxline=120, maxmerged=80, special=ast.AST):
        """Dumps an AST or similar structure:

           - Pretty-prints with indentation
           - Doesn't print line/column/ctx info

        """

        def _inner_dump(node, name=None, indent=''):
            level = indent + indentation
            name = name and name + '=' or ''
            values = list(FuncInfo._iter_node(node))
            if isinstance(node, list):
                prefix, suffix = '%s[' % name, ']'
            elif values:
                prefix, suffix = '%s%s(' % (name, type(node).__name__), ')'
            elif isinstance(node, special):
                prefix, suffix = name + type(node).__name__, ''
            else:
                return '%s%s' % (name, repr(node))
            node = [_inner_dump(a, b, level) for a, b in values if b != 'ctx']
            oneline = '%s%s%s' % (prefix, ', '.join(node), suffix)
            if len(oneline) + len(indent) < maxline:
                return '%s' % oneline
            if node and len(prefix) + len(node[0]) < maxmerged:
                prefix = '%s%s,' % (prefix, node.pop(0))
            node = (',\n%s' % level).join(node).lstrip()
            return '%s\n%s%s%s' % (prefix, level, node, suffix)

        return _inner_dump(node, name, initial_indent)


class ArgParser(argparse.ArgumentParser):
    """
    A simple ArgumentParser to print help when got error.
    """

    def error(self, message):
        self.print_help()
        from gettext import gettext as _

        self.exit(2, _('\n%s: error: %s\n') % (self.prog, message))


class FuncDiffInfo(object):
    """
    An object stores the result of candidate python code compared to referenced python code.
    """

    info_ref = None
    info_candidate = None
    plagiarism_count = 0
    total_count = 0

    @property
    def plagiarism_percent(self):
        return 0 if self.total_count == 0 else (self.plagiarism_count / float(self.total_count))

    def __str__(self):
        if isinstance(self.info_ref, FuncInfo) and isinstance(self.info_candidate, FuncInfo):
            return '{:<4.2}: ref {}, candidate {}'.format(self.plagiarism_percent,
                                                          self.info_ref.func_name + '<' + str(
                                                                  self.info_ref.func_node.lineno) + ':' + str(
                                                                  self.info_ref.func_node.col_offset) + '>',
                                                          self.info_candidate.func_name + '<' + str(
                                                                  self.info_candidate.func_node.lineno) + ':' + str(
                                                                  self.info_candidate.func_node.col_offset) + '>')
        return '{:<4.2}: ref {}, candidate {}'.format(0, None, None)


class UnifiedDiff(object):
    """
    Line diff algorithm to formatted AST string lines, naive but efficiency, result is good enough.
    """

    @staticmethod
    def diff(a, b):
        """
        Simpler and faster implementation of difflib.unified_diff.
        """
        assert a is not None
        assert b is not None
        a = a.func_ast_lines
        b = b.func_ast_lines

        def _gen():
            for group in difflib.SequenceMatcher(None, a, b).get_grouped_opcodes(0):
                for tag, i1, i2, j1, j2 in group:
                    if tag == 'equal':
                        for line in a[i1:i2]:
                            yield ''
                        continue
                    if tag in ('replace', 'delete'):
                        for line in a[i1:i2]:
                            yield '-'
                    if tag in ('replace', 'insert'):
                        for line in b[j1:j2]:
                            yield '+'

        return Counter(_gen())['-']

    @staticmethod
    def total(a, b):
        assert a is not None  # b may be None
        return len(a.func_ast_lines)


class TreeDiff(object):
    """
    Tree edit distance algorithm to AST, very slow and the result is not good for small functions.
    """

    @staticmethod
    def diff(a, b):
        assert a is not None
        assert b is not None

        def _str_dist(i, j):
            return 0 if i == j else 1

        def _get_label(n):
            return type(n).__name__

        def _get_children(n):
            if not hasattr(n, 'children'):
                n.children = list(ast.iter_child_nodes(n))
            return n.children

        import zss
        res = zss.distance(a.func_node, b.func_node, _get_children,
                           lambda node: 0,  # insert cost
                           lambda node: _str_dist(_get_label(node), ''),  # remove cost
                           lambda _a, _b: _str_dist(_get_label(_a), _get_label(_b)), )  # update cost
        return res

    @staticmethod
    def total(a, b):
        #  The count of AST nodes in referenced function
        assert a is not None  # b may be None
        return a.func_node.nsubnodes


class NoFuncException(Exception):
    def __init__(self, source):
        super(NoFuncException, self).__init__('Can not find any functions from code, index = {}'.format(source))
        self.source = source


def detect(pycode_string_list, diff_method=UnifiedDiff, keep_prints=False, module_level=False):
    if len(pycode_string_list) < 2:
        return []

    func_info_list = []
    for index, code_str in enumerate(pycode_string_list):
        root_node = ast.parse(code_str)
        collector = FuncNodeCollector(keep_prints=keep_prints)
        collector.visit(root_node)
        code_utf8_lines = code_str.splitlines(True)
        func_info = [FuncInfo(n, code_utf8_lines) for n in collector.get_function_nodes()]
        if module_level:
            root_node = ast.parse(code_str)
            collector = ModuleNodeCollector(keep_prints=keep_prints)
            collector.visit(root_node)
            module_node = collector.get_module_node()
            module_node.endlineno = len(code_utf8_lines)
            module_info = FuncInfo(module_node, code_utf8_lines)
            func_info.append(module_info)
        func_info_list.append((index, func_info))

    ast_diff_result = []
    index_ref, func_info_ref = func_info_list[0]
    if len(func_info_ref) == 0:
        raise NoFuncException(index_ref)

    for index_candidate, func_info_candidate in func_info_list[1:]:
        func_ast_diff_list = []

        for fi1 in func_info_ref:
            min_diff_value = int((1 << 31) - 1)
            min_diff_func_info = None
            for fi2 in func_info_candidate:
                dv = diff_method.diff(fi1, fi2)
                if dv < min_diff_value:
                    min_diff_value = dv
                    min_diff_func_info = fi2
                if dv == 0:  # entire function structure is plagiarized by candidate
                    break

            func_diff_info = FuncDiffInfo()
            func_diff_info.info_ref = fi1
            func_diff_info.info_candidate = min_diff_func_info
            func_diff_info.total_count = diff_method.total(fi1, min_diff_func_info)
            func_diff_info.plagiarism_count = func_diff_info.total_count - min_diff_value if min_diff_func_info else 0
            func_ast_diff_list.append(func_diff_info)
        func_ast_diff_list.sort(key=operator.attrgetter('plagiarism_percent'), reverse=True)
        ast_diff_result.append((index_candidate, func_ast_diff_list))

    return ast_diff_result


def _profile(fn):
    """
    A simple profile decorator
    :param fn: target function to be profiled
    :return: The wrapper function
    """
    import functools
    import cProfile

    @functools.wraps(fn)
    def _wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        res = fn(*args, **kwargs)
        pr.disable()
        pr.print_stats('cumulative')
        return res

    return _wrapper


def summarize(func_ast_diff_list):
    sum_total_count = sum(func_diff_info.total_count for func_diff_info in func_ast_diff_list)
    sum_plagiarism_count = sum(func_diff_info.plagiarism_count for func_diff_info in func_ast_diff_list)
    if sum_total_count == 0:
        sum_plagiarism_percent = 0
    else:
        sum_plagiarism_percent = sum_plagiarism_count / float(sum_total_count)
    return sum_plagiarism_percent, sum_plagiarism_count, sum_total_count


# @_profile
def main():
    """
    The console_scripts Entry Point in setup.py
    """

    def check_line_limit(value):
        ivalue = int(value)
        if ivalue < 0:
            raise argparse.ArgumentTypeError("%s is an invalid line limit" % value)
        return ivalue

    def check_percentage_limit(value):
        ivalue = float(value)
        if ivalue < 0:
            raise argparse.ArgumentTypeError("%s is an invalid percentage limit" % value)
        return ivalue

    def get_file(value):
        return open(value, 'rb')

    parser = ArgParser(description='A simple plagiarism detection tool for python code')
    parser.add_argument('files', type=get_file, nargs=2,
                        help='the input files')
    parser.add_argument('-l', type=check_line_limit, default=4,
                        help='if AST line of the function >= value then output detail (default: 4)')
    parser.add_argument('-p', type=check_percentage_limit, default=0.5,
                        help='if plagiarism percentage of the function >= value then output detail (default: 0.5)')
    parser.add_argument('-k', '--keep-prints', action='store_true', default=False,
                        help='keep print nodes')
    parser.add_argument('-m', '--module-level', action='store_true', default=False,
                        help='process module level nodes')
    args = parser.parse_args()
    pycode_list = [(f.name, f.read()) for f in args.files]
    try:
        results = detect(
            [c[1] for c in pycode_list],
            keep_prints=args.keep_prints,
            module_level=args.module_level,
        )
    except NoFuncException as ex:
        print('error: can not find functions from {}.'.format(pycode_list[ex.source][0]))
        return

    for index, func_ast_diff_list in results:
        print('ref: {}'.format(pycode_list[0][0]))
        print('candidate: {}'.format(pycode_list[index][0]))
        sum_plagiarism_percent, sum_plagiarism_count, sum_total_count = summarize(func_ast_diff_list)
        print('{:.2f} % ({}/{}) of ref code structure is plagiarized by candidate.'.format(
            sum_plagiarism_percent * 100,
            sum_plagiarism_count,
            sum_total_count,
        ))
        print('candidate function plagiarism details (AST lines >= {} and plagiarism percentage >= {}):'.format(
            args.l,
            args.p,
        ))
        output_count = 0
        for func_diff_info in func_ast_diff_list:
            if len(func_diff_info.info_ref.func_ast_lines) >= args.l and func_diff_info.plagiarism_percent >= args.p:
                output_count = output_count + 1
                print(func_diff_info)

        if output_count == 0:
            print('<empty results>')


if __name__ == '__main__':
    main()
