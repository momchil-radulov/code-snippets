parse_git_branch() {
    git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/ (\1)/'
}
export PS1="\[\033[92m\]\$(date +%T) \[\033[93m\]\W\[\033[91m\]\$(parse_git_branch)\[\033[00m\] $ "

PS1='\t ${debian_chroot:+($debian_chroot)}\[\033[01;34m\]\w\[\033[00m\]$(__git_ps1 "[%s]")$(__dpipe_ps1)\$ '
alias my_project='cd ~/projects/my_project; . ~/projects/my_project/bin/activate'

виж https://stackoverflow.com/questions/749544/pipe-to-from-the-clipboard-in-bash-script
~/.bash_aliases
alias setclip="xclip -selection c"
alias getclip="xclip -selection c -o"
