tmux  # create a new session with and one window with one pane
tmux ls  # list created sessions
tmux a  # append to the last used session
tmux a -t index_of_a_session  # append to a session
# in tmux session
c-b "  # Ctrl + b, " => split a pane horizontally
c-b %  # split a pane vertically
c-b [arrow key]  # move between panes
c-b, c-[arrow key]  # to increase window width/height
c-b c  # create a new window
c-b ,  # rename the current window
c-b index_of_a_window  # go to a window (like virtual desktop)
c-b [  # enter the scroll mode, q - quit scroll mode
c-b t  # show a big clock
c-b ?  # show the help
c-b d  # detach from the tmux
