#!/usr/bin/env bash

foo() {
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
