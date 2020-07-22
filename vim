# execute current line in bash from vim
:.w !bash
# ctags
cd ~/projects/tags
ctags -R --languages=python -f pl.tags ../pylib
:set tags=~/projects/tags/pl.tags,~/projects/tags/project_name.tags
# will run it, be it saved or not
:%w !python
# will run it, only saved
:!python %
