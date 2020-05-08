lsb_release -a

sudo journalctl -u docker.service
cat /etc/group | grep docker
sudo gpasswd -a $USER docker
sudo usermod -aG docker
ls -al /var/run/docker.sock
sudo setfacl -m user:$USER:rw /var/run/docker.sock
