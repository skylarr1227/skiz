#!/usr/bin/env bash
set -e
set -x
black libneko -l 100
git add -A $(find libneko -name "*.py")

