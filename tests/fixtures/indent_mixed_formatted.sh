#!/usr/bin/env bash

function test() {
    while true; do
        for i in $(seq 1 100); do
            local str_with_brackets="[]]]]"
            local str_with_escapes="\"\"\"\""
            # try a command in a $() expansion
            if [ -z "$(echo)" ]; then
                quote_escapes1
                string_with_brackets_inside1
                string_with_brackets_inside2
            fi
        done
    done
}
