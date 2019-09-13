#!/usr/bin/env bash
set -e
set -x
echo -e "\e[1;34mP Y T H O N   S E T U P . P Y   T E S T S\e[0m"
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r discord-py-requirement.txt
python setup.py install
deactivate
