#!/bin/bash

while getopts swx opt; do
    case $opt in
        s) setup=1 ;;
        \?) echo invalid option
            exit ;;
    esac
done

case $x in
    \*) echo "literal star" ;;
    \$) echo "literal dollar" ;;
    \?\?) echo "two escaped" ;;
esac
