#!/bin/bash
# Test case from issue #268 - variables inside single quotes should not be transformed

foo='$bar'
echo '$baz'
greeting='Hello $world'
mixed="$actual" '$literal'
