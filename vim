# execute current line in bash from vim
:.w !bash
# ctags
cd ~/projects/tags
ctags -R --languages=python -f pl.tags ../pylib
:set tags=~/projects/tags/pl.tags,~/projects/tags/project_name.tags
# will run it, be it saved or not
:%w !python
# will run it, after saved
:w | !python %
# append output of an external command
:read !date
# open multiple files
vim *py                  => open mulitple files in vim
:tab all                 => open all open files in new tabs
Ctrl-W Shift-T OR tabe % => open splitted window in a new tab
