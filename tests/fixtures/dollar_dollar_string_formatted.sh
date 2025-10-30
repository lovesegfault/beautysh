#!/bin/bash
grep --quiet --ignore-case "^127\.0\.0\.1\s$$escaped_hostname\s*$" "${hosts_file}"
