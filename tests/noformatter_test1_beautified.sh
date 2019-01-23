#!/bin/bash

function mytest()
{
    echo "Commands in this part will be formatted and indented normally as usual"

	# @formatter:off
	command \
	    --option1 \
	        --option2 \
	            --option3 \
	# @formatter:on
}

# @formatter:off
command \
    --option1 \
        --option2 \
            --option3 \
# @formatter:on
