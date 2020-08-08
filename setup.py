from setuptools import setup

dic = {}
exec(open('pycode_similar/pycode_similar.py').read(), dic)
VERSION = dic['__version__']

if __name__ == '__main__':
    setup(name='pycode_similar',
          version=VERSION,
          description='A simple plagiarism detection tool for python code',
          long_description=open('README.rst').read(),
          author='fyrestone',
          author_email='fyrestone@outlook.com',
          url='https://github.com/fyrestone/pycode_similar',
          license="MIT License",
          package_dir={'': 'pycode_similar'},
          py_modules=['pycode_similar'],
          keywords="code similarity plagiarism moss generic utility",
          platforms=["All"],
          classifiers=['Development Status :: 5 - Production/Stable',
                       'Intended Audience :: Developers',
                       'License :: OSI Approved :: MIT License',
                       'Natural Language :: English',
                       'Operating System :: OS Independent',
                       'Programming Language :: Python :: 2',
                       'Programming Language :: Python :: 3',
                       'Topic :: Software Development :: Libraries',
                       'Topic :: Utilities'],
          entry_points={
              'console_scripts': [
                  'pycode_similar = pycode_similar:main',
              ],
          },
          test_suite='tests',
          zip_safe=False)
