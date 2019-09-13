#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Used on GitLab CI to fetch the current version number, as I am too lazy to keep
it manually up-to-date.
"""
import os
import re
import subprocess
import traceback

RELEASE_ENV = 'PREPARE_RELEASE'
# os.putenv('dryrun', 'True')

SHOULD_USE_TOKEN = os.getenv('USE_TOKEN', 'True') == 'True'

try:
    is_release = os.getenv(RELEASE_ENV, 'False') == 'True'
except:
    is_release = False

if is_release:
    print('Preparing release')
else:
    print('Preparing snapshot')

most_recent_tag_abbrev = '0.0.0'
most_recent_tag_full = '0.0.0-?-???'


def execute(cmd, ignore_error=False):
    print(f'++ $ {cmd}')
    out = None
    try:
        out = subprocess.check_output(cmd, shell=True, universal_newlines=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as ex:
        out = ex.output
        if not ignore_error:
            raise ex
    finally:
        print('--', out)
    return out


execute('git checkout master')

try:
    most_recent_tag_abbrev = execute('git describe --abbrev=0 --tags | head').strip()
except Exception:
    traceback.print_exc()
finally:
    if not is_release:
        if not most_recent_tag_abbrev.endswith('-SNAPSHOT'):
            most_recent_tag_abbrev += '-SNAPSHOT'

print(f'Setting version to {most_recent_tag_abbrev} in PyPi-based configurations, '
      f'and {most_recent_tag_full} elsewhere...')


def replace(file, regex, with_this):
    print(f'Changing version numbers in {file} matching r/{regex}/ggi to {with_this} ...', end=' ')

    with open(file) as fp:
        print('Reading in file')
        contents = fp.read().split('\n')

    new_contents = ''
    for line in contents:
        if re.match(regex, line):
            new_contents += (with_this + '\n')
        else:
            new_contents += (line + '\n')

    while '\n\n\n' in new_contents:
        print('Stripping out triple newline')
        new_contents = new_contents.replace('\n\n\n', '\n\n')

    with open(file, 'w') as fp:
        print('Writing back file')
        fp.write(new_contents)

    print('Done.')


print('Setting version numbers')
replace('libneko/__init__.py', r'^__version__ ', f'__version__ = "{most_recent_tag_abbrev}"')

if is_release:
    try:
        if SHOULD_USE_TOKEN:
            token = os.environ['CI_PUSH_TOKEN']
        else:
            token = ''
    except KeyError:
        print('CANNOT FIND A CI_PUSH_TOKEN VARIABLE CONTAINING THE TOKEN TO PUSH TO THIS REPO')
        print('DEPLOYMENT CANNOT CONTINUE WITHOUT MESSING UP VERSION NUMBERS')
        print('YOUR WORKOUT IS FINISHED. HERE IS SOME CAB FAIR. GOING TO SLEEP MODE')
        exit(254)
    else:
        print('TOKEN FOR REPO R/W ACCESS IS SET TO: ', token[:2] + '*********************')

    print('Starting release-only configuration now')
    if SHOULD_USE_TOKEN:
        execute(f'git remote set-url origin https://oauth2:{token}@gitlab.com/Tmpod/libneko.git')
    else:
        execute(f'git remote set-url origin https://gitlab.com/Tmpod/libneko')
    execute('git config user.name "Libneko CI"')
    execute('git config user.email "Libneko-CI@gitlab.io"')

    matcher = re.match(r'^(\d+)\.(\d+)\.(\d+)(\w*)$', most_recent_tag_abbrev)
    major, minor, micro, extras = matcher.groups()
    print('Ensuring correct version in files in repository')

    execute("git add -A 'libneko/*' 'libneko/*/*'")
    execute(f'git commit -am "Preparing for deployment of {most_recent_tag_abbrev}; ran black [skip ci]"', True)

    if not os.getenv('dryrun', False):
        execute('python setup.py sdist')
    else:
        print('python setup.py sdist  # DRY RUN')

    print(f'Uploading to PyPi as {most_recent_tag_abbrev}')

    print(f"{open('~/.pypirc').read()}")

    if not os.getenv('dryrun', False):
        execute('twine upload dist/* --verbose')
    else:
        print('twine upload dist/*  # DRY RUN')

    print(f'Updating commits to the next snapshot version')
    micro = int(micro) + 1
    most_recent_tag_abbrev_new = f'{major}.{minor}.{micro}{extras}-SNAPSHOT'

    os.unsetenv(RELEASE_ENV)
    execute(f'git tag -a {most_recent_tag_abbrev_new} -m "Preparing for deployment [skip ci]"')
    execute('python scripts/prepare-repo-for-deployment.py')
    execute('black libneko -v -S -l 100')
    execute(f'git commit -am "Updated version to {most_recent_tag_abbrev_new} and formatted code"', True)
    print('Deploying changes to GitLab repository')
    execute('git push origin master')
    execute('git reset --hard origin/master')

    print('Completed.')
