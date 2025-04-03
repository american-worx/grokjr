# app/config/system_dependencies.py

"""
Comprehensive list of built-in and standard library Python modules that do not require pip installation.
This includes sys.builtin_module_names for Python 3.12 and additional common standard library modules.
"""

SYSTEM_DEPENDENCIES = frozenset([
    # Built-in modules from sys.builtin_module_names (Python 3.12)
    '_abc', '_ast', '_bisect', '_blake2', '_codecs', '_codecs_cn', '_codecs_hk', '_codecs_iso2022',
    '_codecs_jp', '_codecs_kr', '_codecs_tw', '_collections', '_contextvars', '_csv', '_datetime',
    '_elementtree', '_frozen_importlib', '_frozen_importlib_external', '_functools', '_hashlib',
    '_heapq', '_imp', '_io', '_json', '_locale', '_lzma', '_md5', '_multibytecodec', '_opcode',
    '_operator', '_pickle', '_posixshmem', '_posixsubprocess', '_queue', '_random', '_sha1',
    '_sha256', '_sha3', '_sha512', '_signal', '_sre', '_stat', '_statistics', '_string', '_struct',
    '_symtable', '_thread', '_tokenize', '_tracemalloc', '_typing', '_warnings', '_weakref',
    '_xxinterpchannels', '_xxsubinterpreters', 'array', 'atexit', 'binascii', 'builtins', 'cmath',
    'errno', 'faulthandler', 'fcntl', 'gc', 'grp', 'itertools', 'marshal', 'math', 'mmap', 'ossaudiodev',
    'posix', 'pwd', 'pyexpat', 'readline', 'resource', 'select', 'spwd', 'sys', 'syslog', 'termios',
    'time', 'unicodedata', 'xxsubtype', 'zlib',

    # Additional common standard library modules (not built-in but included with Python)
    'argparse', 'base64', 'calendar', 'cmd', 'collections', 'configparser', 'copy', 'csv', 'datetime',
    'decimal', 'difflib', 'dis', 'doctest', 'enum', 'fileinput', 'fnmatch', 'fractions', 'ftplib',
    'functools', 'getopt', 'glob', 'gzip', 'hashlib', 'heapq', 'hmac', 'http', 'imaplib', 'importlib',
    'inspect', 'io', 'json', 'keyword', 'linecache', 'locale', 'logging', 'mailbox', 'mimetypes',
    'modulefinder', 'operator', 'optparse', 'os', 'pathlib', 'pickle', 'platform', 'pprint', 'profile',
    'pstats', 'queue', 'random', 're', 'sched', 'shlex', 'shutil', 'signal', 'smtplib', 'socket',
    'sqlite3', 'ssl', 'stat', 'statistics', 'string', 'struct', 'subprocess', 'tempfile', 'textwrap',
    'threading', 'timeit', 'tkinter', 'trace', 'traceback', 'types', 'typing', 'unittest', 'urllib',
    'uu', 'uuid', 'warnings', 'weakref', 'webbrowser', 'xml', 'zipfile'
])

# Note: This list excludes third-party packages like 'scapy', 'requests', etc., which require pip installation.