#!/bin/bash -x
set -e
# Use a mongodb backend by default


if [ -z $ALLEGRO_TEST_BACKEND ]; then
    ALLEGRO_TEST_BACKEND="mongodb"
fi
echo $ALLEGRO_TEST_BACKEND
for backend in $ALLEGRO_TEST_BACKEND; do
    ./setup-test-env-${backend}.sh ./tools/pretty_tox.sh $*
done
