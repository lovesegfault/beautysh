#!/bin/bash
here_launch=(--tab -e "sh -c 'sleep 4; roslaunch launch_scripts here.launch \
   run_minimal:=${run_minimal} --wait; $SHELL -i'")
