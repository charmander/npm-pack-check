#!/usr/bin/env python3
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile


def chomp(s):
    if not s.endswith('\n'):
        raise ValueError('Expected line terminator')

    return s[:-1]


def remove_prefix(s, prefix):
    if not s.startswith(prefix):
        raise ValueError('String does not start with prefix')

    return s[len(prefix):]


REQUIRE_EXTENSIONS = ('.js', '.json', '.node')


def find_requires(js, base):
    for match in re.finditer(r"""
        (?<![.$\w])require\(\s*
            (?P<quote>['"])
            (?=(?P<atomic>
                (?P<name>
                    \.\.?/
                    (?:[^\\]|\\.)*?
                )
                (?P=quote)
            ))(?P=atomic)
        \s*\)
    """, js, flags=re.X):
        name = os.path.join(os.path.dirname(base), match.group('name'))

        if name.endswith('/'):
            name += 'index'
            suffixes = REQUIRE_EXTENSIONS
        else:
            suffixes = ['', *REQUIRE_EXTENSIONS, *('/index' + ext for ext in REQUIRE_EXTENSIONS)]

        name = os.path.normpath(name)

        yield name + '.js', [name + suffix for suffix in suffixes]


with tempfile.TemporaryDirectory() as temp:
    pack = subprocess.run(
        ['npm', 'pack', '--color=always', '--', os.getcwd()],
        stdout=subprocess.PIPE, cwd=temp, check=True)
    pack_name = chomp(pack.stdout.decode('utf-8'))
    pack_path = os.path.join(temp, pack_name)

    if remove_prefix(pack_path, f'{temp}/') == '':
        raise ValueError('Unexpected output from `npm pack`')

    names = set()
    required = []
    package_info = None

    with tarfile.open(pack_path, 'r:*') as tar:
        for entry in tar:
            if entry.isdir():
                continue

            name = remove_prefix(entry.name, 'package/')
            names.add(name)

            if name == 'package.json':
                package_info = json.load(tar.extractfile(entry))
            elif name.endswith('.js'):
                with io.TextIOWrapper(tar.extractfile(entry), 'utf-8') as f:
                    required.extend(find_requires(f.read(), name))

    missing = [p for p in package_info['files'] if p not in names]

    if missing:
        print('\n  \x1b[31m✗\x1b[0m missing:', file=sys.stderr)

        for m in missing:
            print('    - ' + m, file=sys.stderr)

        print(file=sys.stderr)

        raise SystemExit(1)

    potentially_missing = [name for name, options in required if not any(opt in names for opt in options)]

    if potentially_missing:
        print('\n  \x1b[33m!\x1b[0m potentially missing:', file=sys.stderr)

        for m in sorted(potentially_missing):
            print('    - ' + m, file=sys.stderr)

        print(file=sys.stderr)
    else:
        print('\n  \x1b[32m✓\x1b[0m no missing files\n', file=sys.stderr)

    shutil.move(pack_path, pack_name)
    print(pack_name)
