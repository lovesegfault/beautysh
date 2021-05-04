#!/bin/bash

# Verify correct indentation of elif statements (#2, #57)
# https://github.com/lovesegfault/beautysh/issues/2
# https://github.com/lovesegfault/beautysh/issues/57

foo(){
    thing=${1}
    if [[ ${thing} == "bob" ]]
    then
        echo "Yar!"
    elif [[ ${thing} == "jack" ]]
    then
        echo "Yip!"
    else
        echo "Nar"
    fi
}

for thing in "bob" "jim" "jack"
do
    foo "${thing}"
    if (( $? == 0 ))
    then
        echo "Returned success"
    elif (( $? > 0 ))
    then
        echo "No bueno"
    else
        echo "Bad magic"
    fi
done

if [ -f testfile1 ]; then
    echo "1"
elif [ -f testfile2 ]; then
    echo "2"
else
    echo "3"
fi

if [ -f testfile1 ]
then
    echo "1"
elif [ -f testfile2 ]
then
    echo "2"
else
    echo "3"
fi
