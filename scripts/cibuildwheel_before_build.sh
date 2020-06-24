#! /bin/bash

if [[ "$AUDITWHEEL_PLAT" == "manylinux2010_x86_64" ]]; then
    yum install -y libpng-devel freetype-devel
fi

python3 -m pip install -r requirements.txt
