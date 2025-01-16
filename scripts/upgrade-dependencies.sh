#!/bin/bash

set -e

sed -i 's/==/>=/g' requirements.txt
pip install -r requirements.txt --upgrade
sed -i 's/>=/==/g' requirements.txt