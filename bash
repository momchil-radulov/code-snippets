Ctrl + Shift + V -> paste in console

lsb_release -a
# open file with GUI
xdg-open mydoc.pdf
export => show exported env vars
export env_name="${env_name}" => export a env var
unset env_name => remove exported env var
#network
ss, nmcli

#debug bash script
/bin/bash -x scrpt.sh
$cmd &> log => redirect both stderr and stdout 

# !!! Use Bash Strict Mode !!!
see http://redsymbol.net/articles/unofficial-bash-strict-mode/
-e => option instructs bash to immediately exit if any command [1] has a non-zero exit status.
-u => a reference to any variable you haven't previously defined - with the exceptions of $* and $@ - is an error, and causes the program to immediately exit
-o pipefail => if any command in a pipeline fails, that return code will be used as the return code of the whole pipeline. By default, the pipeline's return code is that of the last command
[script.sh]
1 #!/bin/bash
2 set -euo pipefail

# diff with color, like git diff
diff -u /docker/build_docker.sh browsfarm-ci/docker/build_docker.sh | tig

sudo journalctl -u docker.service
cat /etc/group | grep docker
sudo gpasswd -a $USER docker
sudo usermod -aG docker
ls -al /var/run/docker.sock
sudo setfacl -m user:$USER:rw /var/run/docker.sock

/etc/ca-certificates.conf
openssl s_client -connect google.com:443 -CApath /etc/ssl/certs
curl https://google.com:443
# install a certificate to ubuntu
sudo cp foo.crt /usr/share/ca-certificates/extra/foo.crt
sudo dpkg-reconfigure ca-certificates
certutil -d sql:$HOME/.pki/nssdb -A -t "C,," -n "webmail" -i /path_to/foo.crt # for chrome browser

sudo socat -v tcp-listen:80,reuseaddr,fork tcp:localhost:8080
https://stackoverflow.com/questions/22624653/create-a-virtual-serial-port-connection-over-tcp
socat  pty,link=/dev/virtualcom0,raw  tcp:192.168.254.254:8080&
python -m http.server 8080 --bind 127.0.0.1 --cgi

# json
jq -C . movies.json | less -R
cat movies.json | jq -C | less -R
 OR cat movies.json | jq -C .title | less -R
 OR cat movies.json | jq -C . | less -R
cat movies.json | jq keys[] => get top level keys
jq keys; jq '.title | keys'; jq '.title | length'; jq '.title[0] | length'; jq '.title[0] | .first_name';
jq '.title[-1] | .first_name' => get the last element
cat movies.json | jq .title[] => get attribute values from a object

# overload a command
[bin/curlj]
1 #!/bin/bash
2 /usr/bin/curl -H"Content-Type: application/json" "$@"
chmod +x bin/curlj

curl -d @session.json -H 'Content-Type: application/json' localhost:8000/session

# bash auto complete
[.myprogram_cli_autocomplete]
_myprogram_cli_argcomplete() {
    COMPREPLY=( $(./complete_myprogram_cli.py "${COMP_WORDS[@]}") )
}
complete -o nospace -o default -o bashdefault -F _myprogram_cli_argcomplete myprogram_cli.py
complete -o nospace -o default -o bashdefault -F _myprogram_cli_argcomplete ./myprogram_cli.py

# pipeline
## pipe stdout and stderr
command |& grep 'something'
## redirect stderr to stdout
command 2>&1 | grep 'something'
## redirect stderr to stdout and remove stdout
command &> /dev/null | grep 'something'
## with color
python bin/main.py |& colout '(INFO)|(DEBUG)|(ERROR)' green,blue,red #pip install colout
## read stdin pipe with buffer from python:
[readstdio.py]
1 #!/bin/env python
2 import sys
3 import time
4 for line in sys.stdin:
5     time.sleep(10)
6     print(line)
sudo apt install mosquitto-clients
mosquitto_sub -h host_name.com -p 8883 --cafile ca.crt --insecure -u user_name -P password -i user_id -t topic_name/# | ./readstdio.py

# read arduino serial
stty 9600 -F /dev/ttyUSB0 raw -echo
cat /dev/ttyUSB0

## Line buffered stdin. Note use stdbuf -o0 if your data is not line oriented.
   see http://www.pixelbeat.org/programming/stdio_buffering/
tail -f access.log | stdbuf -oL cut -d ' ' -f1 | uniq
## unbuffered stdin for Python3, see https://bugs.python.org/issue18868
   For python use: python -u OR print("Hello world!", flush=True)
[automate.py]
#!/bin/python3
import os, subprocess, time
with open("%s/unbuffered_test.log" % (os.getenv("HOME")), "w") as f:
    with subprocess.Popen(["%s/unbuffered_test.sh" % (os.getenv("HOME"))], stdin=subprocess.PIPE, stdout=f, stderr=f, bufsize=0) as p:
        p.stdin.write(bytes("test\n", encoding="utf-8"))
        time.sleep(10)
[unbuffered_test.sh]
1 #!/bin/sh
2 read INPUT
3 echo $INPUT
4 exit 0

# database
sqlite3 users.db .dump > users.sql
sqlite3 users.db
sudo apt install postgresql-client
[~/.pgpass]
host_name.com:5432:db_name:user_name:password
chmod 600 ~/.pgpass
psql -h host_name.com -U user_name db_name
+
# reverse shell
## server
tail -f nc.log | /bin/bash -i 2>&1 | nc -l localhost 7777 > nc.log
## client
nc localhost 7777

# files
tail -f === less +F (see https://www.brianstorti.com/stop-using-tail/)
# rename files
touch file_name #create a file
sudo su user_name
rename    's/2020-12-21/2020-12-23/' * # multiple files rename
rename -n 's/2020-12-21/2020-12-23/' * # check output whitout real rename
mmv '*abc*' '#1xyz#2' # multiple files mv/cp/link

#zsh
sudo apt instal zsh
https://ohmyz.sh/#install

#ctags
cd ~/projects/tags
ctags -R --languages=python -f pl.tags ../pylib
:set tags=~/projects/tags/pl.tags,~/projects/tags/project_name.tags

#xargs
python -m pip install youtube-dl
cat tonus.txt | xargs -I% youtube-dl %
cat music.txt | xargs -I% youtube-dl -f m4a %
find . | grep py$ | xargs black
find . | grep py$ | xargs -I% pylint %
find . | grep py$ | xargs pylint | less

grep -inr --include '*.py' open ./
grep -l SOME_TEXT * => only show file names

#useful
certbot renew --dry-run
cd ~/bin && wget https://raw.githubusercontent.com/pixelb/ps_mem/master/ps_mem.py && chmod a+x ps_mem.py && cd ~ && source .profile,
bzip2, ca-certificates, curl, git, gnupg,gzip, locales, mercurial, net-tools,
netcat, openssh-client, parallel, sudo, tar, unzip, wget, xvfb, zip

#tooltip, pop up
notify-send msg
