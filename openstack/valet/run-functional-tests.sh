#!/bin/bash -x
set -e
# Use a mongodb backend by default


if [ -z $VALET_TEST_BACKEND ]; then
    VALET_TEST_BACKEND="mongodb"
fi
echo $VALET_TEST_BACKEND
for backend in $VALET_TEST_BACKEND; do
    ./setup-test-env-${backend}.sh ./tools/pretty_tox.sh $*
done
