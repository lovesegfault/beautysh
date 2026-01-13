#!/usr/bin/env bash
# Test case from issue #265 - heredoc inside function

WAITFORIT_cmdname=${0##*/}

usage()
{
    cat << USAGE >&2
Usage:
$WAITFORIT_cmdname -u url [-s] [-t timeout] [-- command args]
-u URL | --url=URL       URL under test
-s | --strict               Only execute subcommand if the test succeeds
-q | --quiet                Don't output any status messages
-t TIMEOUT | --timeout=TIMEOUT
Timeout in seconds, zero for no timeout
-- COMMAND ARGS             Execute command with args after the test finishes
USAGE
    exit 1
}

usage
