pycode_similar
==============

This is a simple plagiarism detection tool for python code, the basic idea is to normalize python AST representation and use difflib to get the modification from referenced code to candidate code. The plagiarism defined in pycode_similar is how many referenced code is plagiarized by candidate code, which means swap referenced code and candidate code will get different result.

It only cost me a couple of hours to implement this tool, so there is still a long way to improve the speed and accuracy, but it already performs great in detecting the plagiarism of new recruits' homeworks in our company.

Compare to Moss
---------------

- pure python implementation
- only contains one source file
- no third-party dependency (except `zss  <https://pypi.python.org/pypi/zss>`_ when use TreeDiff)
- no need to register account for Moss
- no need of network to access Moss

This tool was born before I know there is a `Moss (for a Measure Of Software Similarity)  <https://theory.stanford.edu/~aiken/moss/>`_ to determine the similarity of programs. And I have tried many ways to register account for Stanford Moss, but still can't get a valid account. So, I have no accurate comparison between pycode_similar and Moss.

Installation
--------------

If you don't have much time, just perform

 `$ pip install pycode_similar`

which will install the module(without tests) on your system.

Also, you can just copy & paste the pycode_similar.py which require no third-party dependency.


Usage
--------------

Just use it as a standard command line tool if pip install properly.

.. code-block:: text

	$ pycode_similar
	usage: pycode_similar [-h] [-l L] [-p P] [-k] [-m] files files

	A simple plagiarism detection tool for python code

	positional arguments:
	  files       the input files

	optional arguments:
	  -h, --help          show this help message and exit
	  -l L                if AST line of the function >= value then output detail (default: 4)
	  -p P                if plagiarism percentage of the function >= value then output detail (default: 0.5)
	  -k, --keep-prints   keep print nodes
	  -m, --module-level  process module level nodes

	pycode_similar: error: too few arguments

Of course, you can use it as a python library, too.

.. code-block:: python

	import pycode_similar
	pycode_similar.detect([referenced_code_str, candidate_code_str1, candidate_code_str2, ...], diff_method=pycode_similar.UnifiedDiff, keep_prints=False, module_level=False)
	
	
Implementation
--------------
This tool has implemented two diff methods: line based diff(UnifiedDiff) and tree edit distance based diff(TreeDiff), both of them are run in function AST level.

- UnifiedDiff, diff normalized function AST string lines, naive but efficiency.
- TreeDiff, diff function AST, very slow and the result is not good for small functions. (depends on `zss  <https://pypi.python.org/pypi/zss>`_)

So, when run this tool in cmd, the default diff method is UnifiedDiff. And you can switch to TreeDiff when use it as a library.


Testing
--------------
If you have the source code you can run the tests with

 `$ python pycode_similar/tests/test_cases.py`
 
Or perform

.. code-block:: text

	$ python pycode_similar.py pycode_similar/tests/original_version.py pycode_similar.py

	ref: tests/original_version.py
	candidate: pycode_similar.py
	80.14 % (803/1002) of ref code structure is plagiarized by candidate.
	candidate function plagiarism details (AST lines >= 4 and plagiarism percentage >= 0.5):
	1.0 : ref FuncNodeCollector._mark_docstring_sub_nodes<24:4>, candidate FuncNodeCollector._mark_docstring_sub_nodes<27:4>
	1.0 : ref FuncNodeCollector._mark_docstring_nodes<54:8>, candidate FuncNodeCollector._mark_docstring_nodes<57:8>
	1.0 : ref FuncNodeCollector.generic_visit<69:4>, candidate FuncNodeCollector.generic_visit<72:4>
	1.0 : ref FuncNodeCollector.visit_Str<74:4>, candidate FuncNodeCollector.visit_Str<78:4>
	1.0 : ref FuncNodeCollector.visit_Name<83:4>, candidate FuncNodeCollector.visit_Name<88:4>
	1.0 : ref FuncNodeCollector.visit_Attribute<89:4>, candidate FuncNodeCollector.visit_Name<88:4>
	1.0 : ref FuncNodeCollector.visit_ClassDef<95:4>, candidate FuncNodeCollector.visit_ClassDef<100:4>
	1.0 : ref FuncNodeCollector.visit_FunctionDef<101:4>, candidate FuncNodeCollector.visit_FunctionDef<106:4>
	1.0 : ref FuncInfo.__init__<141:4>, candidate FuncInfo.__init__<161:4>
	1.0 : ref FuncInfo.__str__<151:4>, candidate FuncInfo.__str__<171:4>
	1.0 : ref FuncInfo.func_code<162:4>, candidate FuncInfo.func_code<182:4>
	1.0 : ref FuncInfo.func_code_lines<168:4>, candidate FuncInfo.func_code_lines<188:4>
	1.0 : ref FuncInfo.func_ast<174:4>, candidate FuncInfo.func_ast<194:4>
	1.0 : ref FuncInfo.func_ast_lines<180:4>, candidate FuncInfo.func_ast_lines<200:4>
	1.0 : ref FuncInfo._retrieve_func_code_lines<186:4>, candidate FuncInfo._retrieve_func_code_lines<206:4>
	1.0 : ref FuncInfo._iter_node<208:4>, candidate FuncInfo._iter_node<228:4>
	1.0 : ref FuncInfo._dump<232:4>, candidate FuncInfo._dump<252:4>
	1.0 : ref FuncInfo._inner_dump<242:8>, candidate FuncInfo._inner_dump<262:8>
	1.0 : ref ArgParser.error<267:4>, candidate ArgParser.error<291:4>
	0.95: ref unified_diff<281:0>, candidate UnifiedDiff._gen<339:8>
	0.92: ref FuncNodeCollector.__init__<18:4>, candidate FuncNodeCollector.__init__<20:4>
	0.92: ref FuncNodeCollector.visit_Compare<108:4>, candidate FuncNodeCollector._simple_nomalize<117:8>
	0.89: ref FuncNodeCollector.visit_Expr<79:4>, candidate FuncNodeCollector.visit_Expr<83:4>
	
Click `here  <https://github.com/fyrestone/pycode_similar/commit/149182beee460cbaf21d0995aa442a079ddf1fa9#diff-a30b425e81348c978616747430632fa8>`_
to view this diff -> `0.92: ref FuncNodeCollector.visit_Compare<108:4>, candidate FuncNodeCollector._simple_nomalize<117:8>`

Repository
--------------

The project is hosted on GitHub. You can look at the source here:

 https://github.com/fyrestone/pycode_similar
 
