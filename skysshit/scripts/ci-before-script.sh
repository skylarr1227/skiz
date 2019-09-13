#!/usr/bin/env bash
set -e
set -x
git log -1 --pretty=%B | grep -qiP "^\[skip ci\]$" && echo "Release CI commit; ignoring and killing CI" && exit 0 || true
echo -e "\e[1;34mL I B N E K O   C I   I N I T I A L I Z A T I O N\e[0m"
apt-get update -q
apt-get install git graphviz -qy
python -m pip install --upgrade pip
python -m pip install virtualenv
python -m pip install -r requirements.txt
python -m pip install -r discord-py-requirement.txt
python -c "import discord" || (echo "\e[1;31mDISCORD.PY DID NOT INSTALL PROPERLY! GENERAL FAILURE RUNNING THIS JOB!\e[0m"; false)
python -V
echo -en "\e[1;32mLIBNEKO VERSION "; grep -oiP "(?<=^__version__ = [\"']).*(?=[\"'])" libneko/__init__.py; echo -en "\e[0m"