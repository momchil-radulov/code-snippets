lsb_release -a

sudo journalctl -u docker.service
cat /etc/group | grep docker
sudo gpasswd -a $USER docker
sudo usermod -aG docker
ls -al /var/run/docker.sock
sudo setfacl -m user:$USER:rw /var/run/docker.sock

/etc/ca-certificates.conf
openssl s_client -connect google.com:443 -CApath /etc/ssl/certs
curl https://google.com:443

sudo socat tcp-listen:80,reuseaddr,fork tcp:localhost:8080
python -m http.server 8080 --bind 127.0.0.1 --cgi
