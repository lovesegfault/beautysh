#!/bin/bash
if true; then
    ((x = 1 << 2))
    let y=1<<3
    echo "$x $y"
fi
