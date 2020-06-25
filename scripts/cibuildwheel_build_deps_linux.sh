#! /bin/bash

if hash python3 2>/dev/null; then
    PYTHON=python3
else
    PYTHON=python
fi

echo $($PYTHON --version)

PYTHON_VERSION_MAJOR=$($PYTHON --version | cut -d ' ' -f2 | cut -d '.' -f1)
if [ $PYTHON_VERSION_MAJOR -lt 3 ]; then
    echo 'Python version major must be at least 3!'
    exit 1
fi

$PYTHON -m pip install -r build_requirements.txt

# Required to build matplotlib with i686 images
# yum install -y libpng-devel freetype-devel
# $PYTHON -m pip install -r requirements.txt
