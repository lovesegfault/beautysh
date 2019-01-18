#!/bin/bash

# This is not a script loaded by Beautysh unit tests, rather this verifies
# that all existing unit test scripts are valid Bash sources

THIS_SCRIPT_NAME="$(basename $0)"
THIS_SCRIPT_LOCATION="$(dirname $0)"
ALL_UNIT_TEST_FILES="$(ls -1 $THIS_SCRIPT_LOCATION/*.sh | grep -v $THIS_SCRIPT_NAME)"
for file in $ALL_UNIT_TEST_FILES; do
	echo "Verifying $file ..."
	/bin/bash $file </dev/null >/dev/null 2>&1
	if [ $? -ne 0 ]; then
		echo "Please fix unit test script $file. Bash refuses to load it!"
		exit 2 # fail
	fi
done

exit 0 # success
