lsb_release -a
# open file with GUI
xdg-open mydoc.pdf

#network
ss, nmcli

#debug bash script
/bin/bash -x scrpt.sh

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
python -m http.server 8080 --bind 127.0.0.1 --cgi

# json
jq -C . movies.json | less -R
cat movies.json | jq -C | less -R OR cat movies.json | jq -C .title | less -R OR cat movies.json | jq -C . | less -R

# overload a command
[bin/curlj]
1 #!/bin/bash
2 /usr/bin/curl -H"Content-Type: application/json" "$@"
chmod +x bin/curlj

# pipe
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

tail -f === less +F (see https://www.brianstorti.com/stop-using-tail/)

#zsh
sudo apt instal zsh
https://ohmyz.sh/#install

#ctags
cd ~/projects/tags
ctags -R --languages=python -f pl.tags ../pylib
:set tags=~/projects/tags/pl.tags,~/projects/tags/project_name.tags

#useful
cd ~/bin && wget https://raw.githubusercontent.com/pixelb/ps_mem/master/ps_mem.py && chmod a+x ps_mem.py && cd ~ && source .profile,
bzip2, ca-certificates, curl, git, gnupg,gzip, locales, mercurial, net-tools,
netcat, openssh-client, parallel, sudo, tar, unzip, wget, xvfb, zip
