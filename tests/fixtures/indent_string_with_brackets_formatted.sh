#!/usr/bin/env bash

# https://github.com/lovesegfault/beautysh/issues/29

function test_1() {
    local re='^[\-]?[[0-9]+$'
    # following line contains wrong double TAB:
    echo "hello world"
}

function test_2() {
    RESTORE="$(echo -en '\033[0m')"
    # following line contains wrong TAB:
    echo "hello world"
}
