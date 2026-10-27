#!/usr/bin/env python3
# Compile translations and Qt resources before building an installation package.
#
# Runs the same scripts as the CI "Build resources" workflow:
#   misc/ts2qm.py  - compile OpenNumismat/resources/i18n/lang_*.ts to .qm
#   misc/qrc2py.py - compile OpenNumismat/resources/resources.qrc to resources.py
#
# Pass -u (--update-ts) to refresh OpenNumismat/resources/i18n/lang.ts from the
# sources first (misc/py2ts.py).
#
# Generated .qm and resources.py are stored in the repository and are required
# for running from sources and for building packages.

import os
import subprocess
import sys

base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

steps = []
if '-u' in sys.argv or '--update-ts' in sys.argv:
    steps.append('py2ts.py')
steps.append('ts2qm.py')
steps.append('qrc2py.py')

for step in steps:
    print('Running misc/%s' % step, flush=True)
    result = subprocess.run([sys.executable, os.path.join(base_path, 'misc', step)],
                            cwd=base_path)
    if result.returncode != 0:
        sys.exit(result.returncode)
