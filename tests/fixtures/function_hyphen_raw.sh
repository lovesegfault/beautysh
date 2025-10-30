function clean-vim() {
if [ ! -z "$1" ];
then
rm -rf .cache/$1 .local/state/$1 .local/share/$1
echo "Cleaned .cache/$1 .local/state/$1 .local/share/$1"
else
rm -rf .cache/nvim .local/state/nvim .local/share/nvim
echo "Cleaned .cache/nvim .local/state/nvim .local/share/nvim"
fi
}

function my-test-func() {
echo "test"
}

get-repos() {
echo "repos"
}
