#!/usr/bin/env bash
set -e
set -x
echo -e "\e[1;34mD O C U M E N T A T I O N   G E N E R A T I O N\e[0m"
pip install -Uqr doc/requirements.txt
cd doc
make html 2>&1 | tee -ia test.log
cd ..
mv doc/_build/html/ public/