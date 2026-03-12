#!/bin/bash

if foo="$(echo hej)"; then
echo "hello $foo"
fi

if foo="$(echo \
        hej)"; then
echo "hello $foo"
fi

if foo="$(echo \
        one \
        two)"; then
echo "three lines $foo"
fi
