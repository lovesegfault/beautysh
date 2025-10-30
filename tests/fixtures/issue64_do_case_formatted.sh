#!/bin/bash
while getopts "h" OPT; do
    case $OPT in
        *) true ;;
    esac
done

fn() {
    echo not indented
}
