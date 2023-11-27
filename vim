Ctrl - d -> complete suggestions
:set ruler
:set ruler! OR :set noruler
:set wildmenu
:h -> help, :h command, Ctrl - ], Ctrl - o, Ctrl - w Ctrl - w

# position
H - top
M - middle
L - botttom
zt - move top
zz - move middle
zb - move bottom
Ctrl - f, ^f - page down
Ctrl - b     - page up

# insert mode
80i*       - insert 80 *
5osometext - 5 new lines with sometext
Shift + r  - replace mode
:reg
"0p - insert from 0 register, yy - register

# split
Ctrl - ws - split
Ctrl - wv - vertically split
Ctrl - ww - move between window

# execute current line in bash from vim
:.w !bash
# code reformat
gg=G
:%!black -q -
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
vim -p $(ls | grep '.py$')
vim -p $(cat search | cut -f1 -d: | uniq)

# sessions
see https://www.redhat.com/sysadmin/vim-abbreviations
:mksession ~/mysession.vim
:source ~/mysession.vim
vim -S ~/mysession.vim

mkdir .vim && cd .vim
git clone --depth 1 https://github.com/codota/tabnine-vim

# search and replace
# int(10) => int ; smallint(6) => smallint
:%s/int([0-9]\+)/int/g
