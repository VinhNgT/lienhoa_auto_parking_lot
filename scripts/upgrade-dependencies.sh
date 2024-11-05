#!/bin/bash

set -e

pip freeze > requirements.txt.temp
sed -i 's/==/>=/g' requirements.txt.temp
pip install -r requirements.txt.temp --upgrade
rm requirements.txt.temp

pip freeze > requirements.txt