#!/usr/bin/env bash

function test_1() {
    T=$(echo "\"a\"")
    echo "command to indent"
}

function test_2() {
    local EVIL_STRING="{\"time\":{\"last\":{\"value\":1,\"type\":\"days\",\"clockType\":\"days\",\"start\":${TEST_START_TIME}},\"to\":${TEST_END_TIME},\"from\":${TEST_START_TIME_PLUS_ONE}}, \
\"categories\":{\"category\":[${CATEGORY_FOR_EMPIRIX_EXMS_QUERY}]},\"requestedRows\":1000,\
\"advancedFilters\":[{\"groupOperator\":\"or\",\"advancedFilter\":[{\"filter\":[{\"name\":\"${PARAM}\",\"type\":\"string\",\"condition\":\"=\",\"value\":[\"${VALUE}\"]}],\
\"filterOperator\":\"and\"}],\"asdr\":\"common\"}]}"
    echo "command to indent"
}
