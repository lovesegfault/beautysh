#!/usr/bin/env bash

# this small snippet is to test beautysh function-style detector
# NOTE: using the string "function" in the function name itself we do a deeper test

function_style1a()
{
    echo "test"
}

function_style1b()
{
    echo "test"
}

function_style1c()
{
    echo "test"
}

function_style1d() {
    echo "test"
}

function_style2a()
{
    echo "test"
}

function_style2b() {
    echo "test"
}

function_style3a()
{
    echo "test"
}

function_style3b()
{
    echo "test"
}

function_style3c()
{
    echo "test"
}

function_style3d() {
    echo "test"
}

function::style3e() {
    echo "test"
}

function@style3f() {
    echo "test"
}
