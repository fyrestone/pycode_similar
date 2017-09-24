__author__ = 'fyrestone@outlook.com'

import sys
import ast
import difflib
import operator
import argparse
import itertools
import collections


class FuncNodeCollector(ast.NodeTransformer):
    """
    Clean node attributes, delete the attributes that are not helpful for recognition repetition.
    Then collect all function nodes.
    """

    def __init__(self):
        super(FuncNodeCollector, self).__init__()
        self._curr_class_names = []
        self._func_nodes = []
        self._last_node_lineno = -1

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
        self._last_node_lineno = max(getattr(node, 'lineno', -1), self._last_node_lineno)
        self._mark_docstring_sub_nodes(node)
        return super(FuncNodeCollector, self).generic_visit(node)

    def visit_Str(self, node):
        del node.s
        self.generic_visit(node)
        return node

    def visit_Expr(self, node):
        if not self._is_docstring(node):
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

    def visit_ClassDef(self, node):
        self._curr_class_names.append(node.name)
        self.generic_visit(node)
        self._curr_class_names.pop()
        return node

    def visit_FunctionDef(self, node):
        node.name = '.'.join(itertools.chain(self._curr_class_names, [node.name]))
        self._func_nodes.append(node)
        self.generic_visit(node)
        node.endlineno = self._last_node_lineno
        return node

    def visit_Compare(self, node):
        # Eq simple case normalized
        if node.ops and len(node.ops) == 1 and type(node.ops[0]).__name__ == 'Eq':
            if node.left and node.comparators and len(node.comparators) == 1:
                left, right = node.left, node.comparators[0]
                if cmp(type(left).__name__, type(right).__name__) > 0:
                    left, right = right, left
                    node.left = left
                    node.comparators = [right]
        self.generic_visit(node)
        return node

    def clear(self):
        self._func_nodes = []

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
        assert isinstance(func_node, ast.FunctionDef)
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
        if not isinstance(func_node, ast.FunctionDef):
            return []
        if not isinstance(code_lines, collections.Sequence) or isinstance(code_lines, basestring):
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
    def error(self, message):
        self.print_help()
        from gettext import gettext as _

        self.exit(2, _('\n%s: error: %s\n') % (self.prog, message))


class FuncDiffInfo(object):
    info_target = None
    info_source = None
    target_copy_percent = 0
    target_copy_line_count = 0


def unified_diff(a, b):
    r"""
    Simpler and faster implementation of difflib.unified_diff.
    """

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


def pycopydetector(args):
    ast_diff_result = []
    func_info_items = []

    for f in args.files:
        code_str = f.read()
        root_node = ast.parse(code_str)
        collector = FuncNodeCollector()
        collector.visit(root_node)
        code_utf8_lines = code_str.splitlines(True)
        func_info_list = [FuncInfo(n, code_utf8_lines) for n in collector.get_function_nodes()]
        func_info_items.append((f.name, func_info_list))

    if len(func_info_items) < 2:
        return

    for i in xrange(1, len(func_info_items)):
        name1, func_list1 = func_info_items[0]
        name2, func_list2 = func_info_items[i]
        func_ast_diff_list = []
        for fi1 in func_list1:
            min_diff_line_count = sys.maxint
            min_diff_fi2 = None
            for fi2 in func_list2:
                dv = unified_diff(fi1.func_ast_lines, fi2.func_ast_lines)
                counter = collections.Counter(dv)
                if counter['-'] + counter['+'] < min_diff_line_count:
                    min_diff_line_count = counter['-']
                    min_diff_fi2 = fi2

            func_diff_info = FuncDiffInfo()
            func_diff_info.info_target = fi1
            func_diff_info.info_source = min_diff_fi2
            func_diff_info.target_copy_percent = 1 - min_diff_line_count / float(len(fi1.func_ast_lines))
            func_diff_info.target_copy_line_count = len(fi1.func_ast_lines) - min_diff_line_count
            func_ast_diff_list.append(func_diff_info)
        func_ast_diff_list.sort(key=operator.attrgetter('target_copy_percent'), reverse=True)
        ast_diff_result.append((name1, name2, func_ast_diff_list))

    for name1, name2, func_ast_diff_list in ast_diff_result:
        print('target: {}'.format(name1))
        print('source: {}'.format(name2))
        total_ast_lines = sum(len(func_diff_info.info_target.func_ast_lines) for func_diff_info in func_ast_diff_list)
        copy_ast_lines = sum(func_diff_info.target_copy_line_count for func_diff_info in func_ast_diff_list)
        print('{:.2f} % ({}/{}) of target code structure copy from source.'.format(
            copy_ast_lines / float(total_ast_lines) * 100,
            copy_ast_lines,
            total_ast_lines))
        print('target function copy details (AST lines > 3 and copy percentage > 0.5):')
        for func_diff_info in func_ast_diff_list:
            if len(func_diff_info.info_target.func_ast_lines) > 3 and func_diff_info.target_copy_percent > 0.5:
                print('{:<4.2}: target {}, source {}'.format(func_diff_info.target_copy_percent,
                                                             func_diff_info.info_target.func_name + '<' + str(
                                                                 func_diff_info.info_target.func_node.lineno) + ':' + str(
                                                                 func_diff_info.info_target.func_node.col_offset) + '>',
                                                             func_diff_info.info_source.func_name + '<' + str(
                                                                 func_diff_info.info_source.func_node.lineno) + ':' + str(
                                                                 func_diff_info.info_source.func_node.col_offset) + '>'))


if __name__ == '__main__':
    parser = ArgParser(description='A python code copy detection tool')
    parser.add_argument('files', type=file, nargs=2,
                        help='the input files')
    args = parser.parse_args()
    pycopydetector(args)
