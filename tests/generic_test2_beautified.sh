#!/bin/bash
# ref-params.sh: Dereferencing a parameter passed to a function.
#                (Complex Example) -- taken from https://www.tldp.org/LDP/abs/html/complexfunct.html#DEREFERENCECL

ITERATIONS=3  # How many times to get input.
icount=1

function my_read() {
    #  Called with my_read varname,
    #+ outputs the previous value between brackets as the default value,
    #+ then asks for a new value.

    local local_var

    echo -n "Enter a value "
    eval 'echo -n "[$'$1'] "'  #  Previous value.
    # eval echo -n "[\$$1] "     #  Easier to understand,
    #+ but loses trailing space in user prompt.
    read local_var
    [ -n "$local_var" ] && eval $1=\$local_var

    # "And-list": if "local_var" then set "$1" to its value.
}

echo

while [ "$icount" -le "$ITERATIONS" ]
do
    my_read var
    echo "Entry #$icount = $var"
    let "icount += 1"
    echo
done


# Thanks to Stephane Chazelas for providing this instructive example.

exit 0