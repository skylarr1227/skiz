#!/usr/bin/env bash
set -e
set -x

# Run me to quickly generate and preview the documentation!
# Specify a port as the first argument, or it will default to 8000
# See: https://stackoverflow.com/questions/7943751/what-is-the-python-3-equivalent-of-python-m-simplehttpserver
# Assumes all dependencies actually exist already.

echo -e "\e[1;34mD O C U M E N T A T I O N   P R E V I E W\e[0m"
PYTHON=$(which python3 || which python)

PORT=8000
if [[ ! -z "${1}" ]]; then
    PORT=${1}
fi

cd doc
make clean html || exit ${?}
cd _build/html
echo -e "\n\e[1;32mPLEASE GO TO http://localhost:${PORT}/ TO VIEW THE DOCUMENTATION!\e[0m\n"
${PYTHON} -m http.server ${PORT}
