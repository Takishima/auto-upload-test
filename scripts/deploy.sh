#! /bin/bash

section_start()
{
    export CURRENT_SECTION=$1
    travis_fold start $CURRENT_SECTION
    travis_time_start
}

section_finish()
{
    travis_time_finish
    travis_fold stop $CURRENT_SECTION
}

# ------------------------------------------------------------------------------

DIST_DIR=$1
shift

# ==============================================================================

section_start "deploy.init"
cat << EOF > ~/.pypirc
[distutils]
index-servers=
    pypi

[pypi]
repository: $DEPLOY_URL
username: $DEPLOY_USERNAME
password: $DEPLOY_PASSWORD
EOF
section_finish

section_start "deploy.build"
python3 setup.py sdist
python3 -m cibuildwheel --output-dir dist/
section_finish

section_start "deploy.check"
python3 -m twine check $DIST_DIR
section_finish

section_start "deploy.upload"
python3 -m twine upload "$@" -r pypi dist/*
section_finish

