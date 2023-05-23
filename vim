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
80i* - insert 80 *
:reg
"0p - insert from 0 register, yy - register

# split
Ctrl - ws - split
Ctrl - wv - vertically split
Ctrl - ww - move between window

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
vim -p $(ls | grep '.py$')
vim -p $(cat search | cut -f1 -d: | uniq)

# sessions
see https://www.redhat.com/sysadmin/vim-abbreviations
:mksession ~/mysession.vim
:source ~/mysession.vim
vim -S ~/mysession.vim

# abbreviations (in .vimrc)
:ab os operating system  # create
some text os[Space bar or Enter]
To prevent an abbreviation from expanding, type Ctrl+V before entering the abbreviated word
:ab teh the  # autocorrect  mistakes
:iab p <p></p><esc>3hi  # code snippets, after <esc> normal/command mode, cursor movement and return to insert mode

[.vimrc] FILE
"Вырубаем режим совместимости с VI:
set nocompatible

"Включаем распознавание типов файлов и типо-специфичные плагины:
filetype on
filetype plugin on
syntax on "Включить подсветку синтаксиса

" Настройки табов для Python, согласно рекоммендациям
set tabstop=4
set shiftwidth=4
set smarttab
set expandtab "Ставим табы пробелами
set softtabstop=4 "4 пробела в табе

" Вырубаем черточки на табах
set showtabline=1
set nu "Включаем нумерацию строк

"Автоотступ
"set autoindent
""Подсвечиваем все что можно подсвечивать
let python_highlight_all = 1 
"Включаем 256 цветов в терминале, мы ведь работаем из иксов?
""Нужно во многих терминалах, например в gnome-terminal
set t_Co=256

"Настройка omnicomletion для Python (а так же для js, html и css)
autocmd FileType python set omnifunc=pythoncomplete#Complete
"autocmd FileType javascript set omnifunc=javascriptcomplete#CompleteJS
"autocmd FileType html set omnifunc=htmlcomplete#CompleteTags
"autocmd FileType css set omnifunc=csscomplete#CompleteCSS

"set rtp+=~/.vim/tabnine-vim
[.vimrc] END
mkdir .vim && cd .vim
git clone --depth 1 https://github.com/codota/tabnine-vim
