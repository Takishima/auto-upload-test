#! /bin/bash

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

echo 'Building source distribution'
$PYTHON_EXEC setup.py sdist

echo 'Building binary distributions'
$PYTHON_EXEC -m cibuildwheel --output-dir dist/

# Make sure that twine is installed (mostly for Mac OS)
$PYTHON_EXEC -m pip install twine

echo 'Running twine check'
$PYTHON_EXEC -m twine check $DIST_DIR

echo 'Running twine upload'
$PYTHON_EXEC -m twine upload "$@" -r pypi dist/*

