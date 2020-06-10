### How to ignore new files
#### Globally
.gitignore
#### Locally
.git/info/exclude

### temporary undo changes in a file and after that, return changes
git stash push project_name/appsettings.json  
git stash pop
### show and clear stash stack
git stash list  
git stash clear
### revert last commit
git reset --soft HEAD~1
### undo last add command
git reset
