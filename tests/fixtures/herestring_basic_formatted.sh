#!/bin/bash

function get_resource {
    IFS="$DELIMITER" read -r -a ARR <<< "$temp"
}
