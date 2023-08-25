[~/.vimrc]
" Общи настройки
set number                " Показва номера на редовете
set showcmd               " Показва последната въведена команда
set cursorline            " Осветява текущия ред
set wildmenu              " Показва възможните допълнения в командния ред
set incsearch             " Показва резултатите от търсенето докато въвеждате
set hlsearch              " Осветява резултатите от търсенето
filetype plugin on        " Включва поддръжка за различни типове файлове
syntax enable             " Включва синтаксисно оцветяване

" Настройки за Python
augroup python_settings
    autocmd!
    autocmd FileType python set tabstop=4
    autocmd FileType python set shiftwidth=4
    autocmd FileType python set smarttab
    autocmd FileType python set expandtab
    autocmd FileType python set softtabstop=4
    autocmd FileType python set autoindent
    autocmd FileType python set textwidth=79
    autocmd FileType python set smartindent
    autocmd FileType python set wrap
    autocmd FileType python set linebreak
    autocmd FileType python set showmatch
    autocmd FileType python set matchpairs+=<:>
    autocmd FileType python syntax on
    autocmd FileType python filetype plugin indent on
    "$ pip install black
    "autocmd FileType python set formatprg=black\ -
augroup END

" Настройки за PHP
augroup php_settings
    autocmd!
    autocmd FileType php set tabstop=4              " Задава броя на пробелите в табулацията на 4
    autocmd FileType php set shiftwidth=4           " Задава ширината на индентацията на 4 пробела
    autocmd FileType php set smarttab               " Умни табулации
    autocmd FileType php set expandtab              " Замества табулации с пробелите
    autocmd FileType php set softtabstop=4          " Задава 4 пробела в табулация
    autocmd FileType php set autoindent             " Автоматична индентация
    autocmd FileType php set textwidth=0            " Без ограничение на ширината на реда
    autocmd FileType php set smartindent            " Умна индентация
    autocmd FileType php set wrap                   " Пренасочва дългите редове
    autocmd FileType php set showmatch              " Показва съответстващите скоби
    autocmd FileType php set matchpairs+=<:>        " Добавя < и > към съответстващите скоби
    autocmd FileType php syntax on                  " Включва синтаксисно оцветяване
    autocmd FileType php filetype plugin indent on  " Включва индентационни плъгини
    "$ composer global require friendsofphp/php-cs-fixer
    "autocmd FileType php set formatprg=php-cs-fixer\ fix\ --using-cache=no\ -
augroup END

" Ако искате допълнителни настройки за други типове файлове, можете да ги добавите тук



[~/.vimrc] abbreviations
:ab os operating system  # create
some text os[Space bar or Enter]
To prevent an abbreviation from expanding, type Ctrl+V before entering the abbreviated word
:ab teh the  # autocorrect  mistakes
:iab p <p></p><esc>3hi  # code snippets, after <esc> normal/command mode, cursor movement and return to insert mode



[~/.vimrc] разни други примерни неща
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
