#!/bin/bash
# Test case from issue #265 - quoted empty case patterns

case "$input" in
"")
echo "empty double quote"
;;
'')
echo "empty single quote"
;;
" ")
echo "single space"
;;
*)
echo "other"
;;
esac
