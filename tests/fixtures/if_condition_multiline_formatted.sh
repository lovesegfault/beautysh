#!/usr/bin/env bash

function test() {
    # do basic argument checks
    if [ "$A" == "true" ] || [ "$A" == "false" ] || [ "$A" == "noconflicts" ] || [ "$B" == "true" ] || [ "$B" == "false" ] || [ "$B" == "noconflicts" ] || [ "$C" == "true" ] || [ "$C" == "false" ]; then
        printerr "Internal error: invalid function call argument"
        exit 2
    fi
}
