#!/bin/bash
# Test heredocs with quoted terminators - variables should not be transformed

# Single-quoted terminator - no expansion
cat <<'EOF'
$foo should not expand
$bar should not expand
EOF

# Double-quoted terminator - no expansion
cat <<"END"
$baz should not expand
$qux should not expand
END

# Unquoted terminator - expansion happens
cat <<EXPAND
$actual should expand
EXPAND

# Regular variable outside heredoc
echo $normal
