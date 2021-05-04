#!/usr/bin/env bash

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
