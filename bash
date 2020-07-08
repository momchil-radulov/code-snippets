lsb_release -a
# open file with GUI
xdg-open mydoc.pdf

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

# pipe
read stdin pipe from python:
[readstdio.py]
1 #!/bin/env python
2 import sys
3 import time
4 
5 for line in sys.stdin:
6     time.sleep(10)
7     print(line)
sudo apt install mosquitto-clients
mosquitto_sub -h host_name.com -p 8883 --cafile ca.crt --insecure -u user_name -P password -i user_id -t topic_name/# | ./readstdio.py

# database
sqlite3 users.db .dump > users.sql
sqlite3 users.db
sudo apt install postgresql-client
[~/.pgpass]
host_name.com:5432:db_name:user_name:password
chmod 600 ~/.pgpass
psql -h host_name.com -U user_name db_name
