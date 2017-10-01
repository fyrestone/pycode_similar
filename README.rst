pycode_similar
==============

This is a simple plagiarism detection tool for python code, the basic idea is to normalize python AST representation and use difflib to get the modification from referenced code to candidate code. The plagiarism defined in pycode_similar is how many referenced code is plagiarized by candidate code, which means swap referenced code and candidate code will get different result.

It only cost me a couple of hours to implement this tool, so there is still a long way to improve the speed and accuracy, but it already performs great in detecting the plagiarism of new recruits' homeworks in our company.


Installation
--------------

If you don't have much time, just perform

 `$ pip install pycode_similar`

which will install the module(without tests) on your system.

Also, you can just copy & paste the pycode_similar.py which require no third-party dependency.


Usage
--------------

Just use it as a standard command line tool.

.. code-block:: text

	$ python pycode_similar.py
	usage: pycode_similar.py [-h] [-l L] [-p P] files files

	A simple plagiarism detection tool for python code

	positional arguments:
	  files       the input files

	optional arguments:
	  -h, --help  show this help message and exit
	  -l L        if AST line of the function >= value then output detail
				  (default: 4)
	  -p P        if plagiarism percentage of the function >= value then output
				  detail (default: 0.5)

	pycode_similar.py: error: too few arguments
	
Of course, you can use it as a python library, too.

.. code-block:: python

	import pycode_similar
	pycode_similar.detect([referenced_code_str, candidate_code_str1, candidate_code_str2, ...])

Testing
--------------
If you have the source code you can run the tests with

 `$ python pycode_similar/tests/test_cases.py`
 
Or perform

.. code-block:: text

	$ python pycode_similar.py pycode_similar/tests/original_version.py pycode_similar.py

	ref: tests/original_version.py
	candidate: pycode_similar.py
	84.22 % (907/1077) of ref code structure is plagiarized by candidate.
	candidate function plagiarism details (AST lines >= 4 and plagiarism percentage >= 0.5):
	1.0 : ref FuncNodeCollector.__init__<18:4>, candidate FuncNodeCollector.__init__<18:4>
	1.0 : ref FuncNodeCollector._mark_docstring_sub_nodes<24:4>, candidate FuncNodeCollector._mark_docstring_sub_nodes<24:4>
	1.0 : ref FuncNodeCollector._mark_docstring_nodes<54:8>, candidate FuncNodeCollector._mark_docstring_nodes<54:8>
	1.0 : ref FuncNodeCollector.generic_visit<69:4>, candidate FuncNodeCollector.generic_visit<69:4>
	1.0 : ref FuncNodeCollector.visit_Str<74:4>, candidate FuncNodeCollector.visit_Str<74:4>
	1.0 : ref FuncNodeCollector.visit_Expr<79:4>, candidate FuncNodeCollector.visit_Expr<79:4>
	1.0 : ref FuncNodeCollector.visit_Name<83:4>, candidate FuncNodeCollector.visit_Name<83:4>
	1.0 : ref FuncNodeCollector.visit_Attribute<89:4>, candidate FuncNodeCollector.visit_Name<83:4>
	1.0 : ref FuncNodeCollector.visit_ClassDef<95:4>, candidate FuncNodeCollector.visit_ClassDef<95:4>
	1.0 : ref FuncNodeCollector.visit_FunctionDef<101:4>, candidate FuncNodeCollector.visit_FunctionDef<101:4>
	1.0 : ref FuncInfo.__init__<141:4>, candidate FuncInfo.__init__<154:4>
	1.0 : ref FuncInfo.__str__<151:4>, candidate FuncInfo.__str__<164:4>
	1.0 : ref FuncInfo.func_code<162:4>, candidate FuncInfo.func_code<175:4>
	1.0 : ref FuncInfo.func_code_lines<168:4>, candidate FuncInfo.func_code_lines<181:4>
	1.0 : ref FuncInfo.func_ast<174:4>, candidate FuncInfo.func_ast<187:4>
	1.0 : ref FuncInfo.func_ast_lines<180:4>, candidate FuncInfo.func_ast_lines<193:4>
	1.0 : ref FuncInfo._retrieve_func_code_lines<186:4>, candidate FuncInfo._retrieve_func_code_lines<199:4>
	1.0 : ref FuncInfo._iter_node<208:4>, candidate FuncInfo._iter_node<221:4>
	1.0 : ref FuncInfo._dump<232:4>, candidate FuncInfo._dump<245:4>
	1.0 : ref FuncInfo._inner_dump<242:8>, candidate FuncInfo._inner_dump<255:8>
	1.0 : ref ArgParser.error<267:4>, candidate ArgParser.error<284:4>
	1.0 : ref unified_diff<281:0>, candidate unified_diff<313:0>
	0.85: ref FuncNodeCollector.visit_Compare<108:4>, candidate FuncNodeCollector._simple_nomalize<110:8>
	
Click here to view this -> 0.85: ref FuncNodeCollector.visit_Compare<108:4>, candidate FuncNodeCollector._simple_nomalize<110:8>

Repository
--------------

The project is hosted on GitHub. You can look at the source here:

 https://github.com/fyrestone/pycode_similar
 