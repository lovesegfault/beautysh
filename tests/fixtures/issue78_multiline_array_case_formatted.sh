#!/bin/bash

quiet="true"
files=()

for arg in "${@}"; do
    case "${arg}" in
        "-v" | "--verbose")
            quiet="false"
            ;;
        *)
            files+=(
                "${arg}"
            )
            ;;
    esac
done
