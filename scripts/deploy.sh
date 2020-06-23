#! /usr/bin/env bash

DIST_DIR=$1
shift

# ==============================================================================

echo 'Setting up default repository'
cat << EOF > ~/.pypirc
[distutils]
index-servers=
    pypi

[pypi]
repository: $DEPLOY_URL
username: $DEPLOY_USERNAME
password: $DEPLOY_PASSWORD
EOF

PYTHON=python3
if [[ ! -e $PYTHON ]]; then
    PYTHON=python
fi

echo $($PYTHON --version)

echo 'Installing dependencies'
$PYTHON -m pip install -U wheel cibuildwheel twine

echo 'Building source distribution'
$PYTHON setup.py sdist

echo 'Building binary distributions'
$PYTHON -m cibuildwheel --output-dir dist/

# Make sure that twine is installed (mostly for Mac OS)
$PYTHON -m pip install twine

echo 'Running twine check'
$PYTHON -m twine check $DIST_DIR

echo 'Running twine upload'
$PYTHON -m twine upload "$@" -r pypi dist/*

