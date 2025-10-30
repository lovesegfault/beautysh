#!/bin/bash
echo "${VAR:-default}"
echo "${VAR#prefix}"
echo "${arr[1]}"
echo "${!VAR}"
echo "${#VAR}"
