#!/bin/bash

# this small snippet is to test against regressions for issue#29
#    https://github.com/bemeurer/beautysh/issues/29

function mytest()
{
    local re='^[\-]?[[0-9]+$'
    
    # following line contains wrong double TAB:
		echo "hello world"
}

function mytest2()
{
    RESTORE="$(echo -en '\033[0m')"

    # following line contains wrong TAB:
	echo "hello world"
}
