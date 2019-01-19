#!/bin/bash
# max2.sh: Maximum of two LARGE integers. -- taken from https://www.tldp.org/LDP/abs/html/complexfunct.html#MAX2

#  This is the previous "max.sh" example,
#+ modified to permit comparing large integers.

EQUAL=0             # Return value if both params equal.
E_PARAM_ERR=-99999  # Not enough params passed to function.
#           ^^^^^^    Out of range of any params that might be passed.

max2 ()             # "Returns" larger of two numbers.
{
if [ -z "$2" ]
then
  echo $E_PARAM_ERR
  return
fi

if [ "$1" -eq "$2" ]
then
  echo $EQUAL
  return
else
  if [ "$1" -gt "$2" ]
  then
    retval=$1
  else
    retval=$2
  fi
fi

echo $retval        # Echoes (to stdout), rather than returning value.
                    # Why?
}


return_val=$(max2 33001 33997)
#            ^^^^             Function name
#                 ^^^^^ ^^^^^ Params passed
#  This is actually a form of command substitution:
#+ treating a function as if it were a command,
#+ and assigning the stdout of the function to the variable "return_val."


# ========================= OUTPUT ========================
if [ "$return_val" -eq "$E_PARAM_ERR" ]
  then
  echo "Error in parameters passed to comparison function!"
elif [ "$return_val" -eq "$EQUAL" ]
  then
    echo "The two numbers are equal."
else
    echo "The larger of the two numbers is $return_val."
fi
# =========================================================
  
exit 0

#  Exercises:
#  ---------
#  1) Find a more elegant way of testing
#+    the parameters passed to the function.
#  2) Simplify the if/then structure at "OUTPUT."
#  3) Rewrite the script to take input from command-line parameters.