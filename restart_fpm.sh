lockResult=$(lsof /root/git/db/users.db | wc -l 2>&1)
if [ "$lockResult" -gt 2 ]; then
    currentDate=`date`
    /usr/sbin/service "php7.0-fpm" restart
    echo "$currentDate " >> /root/git/db/restart_fpm.log;
    echo "Restart php7.0-fpm" >> /root/git/db/restart_fpm.log;
else
    lockResultOK="OK"
fi
