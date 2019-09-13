#!/usr/bin/env bash
set -e
set -x
echo -e "\e[1;34mP Y T H O N   U N I T   T E S T S\e[0m"
python -m coverage run --timid --branch  --source=libneko -m libneko.test 2>&1 || (echo -e "\e[1;31mOne or more tests failed\e[0m" && false)
python -m coverage report -m
