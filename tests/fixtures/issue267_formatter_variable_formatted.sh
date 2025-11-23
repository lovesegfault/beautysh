#!/bin/bash
# Test case from issue #267 - @formatter:off/on with --variable-style braces

echo "${foo}"
# @formatter:off
echo "$bar"
# @formatter:on
echo "${baz}"

if true; then
# @formatter:off
echo "$disabled"
# @formatter:on
    echo "${enabled}"
fi
