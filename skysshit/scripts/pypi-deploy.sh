#!/usr/bin/env bash
echo -e "\e[1;34mD E P L O Y M E N T   T O   P Y P I   R E P O S I T O R I E S\e[0m"
pip install -U twine
pip install -U black
echo "[pypi]" > ~/.pypirc
echo "username: "${PYPI_USER} >> ~/.pypirc
echo "password: "${PYPI_PASSWORD} >> ~/.pypirc
cat ~/.pypirc


# Create the release version.
export PREPARE_RELEASE=True
python scripts/prepare-repo-for-deployment.py
