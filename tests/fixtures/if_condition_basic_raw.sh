#!/usr/bin/env bash

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
