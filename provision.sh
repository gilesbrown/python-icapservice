#!/bin/bash

sudo apt-get install squid -y

sudo apt-get install python-pip -y
sudo /usr/bin/pip install virtualenv
sudo /usr/bin/pip install virtualenvwrapper

sudo -i -u vagrant mkvirtualenv icapservice

function append_line() {
    local line=${1}
    local file=${2}
    grep -q -F "$line" $file || sudo -u vagrant echo "$line" >> $file
}

append_line "source /usr/local/bin/virtualenvwrapper.sh" ~vagrant/.bash_profile
sudo -i -u vagrant mkvirtualenv icapservice
sudo -i -u vagrant sh -c "~/.virtualenvs/icapservice/bin/pip install --upgrade pip"
sudo -i -u vagrant sh -c "cd /vagrant; ~/.virtualenvs/icapservice/bin/python setup.py develop"
append_line "workon icapservice" ~vagrant/.bash_profile

echo "INSTALL SQUID CONF"
cp /vagrant/squid.conf /etc/squid3/squid.conf

echo "TELL SQUID TO RELOAD CONFIG"
sudo sh -c "start squid3 || /usr/sbin/squid3 -k reconfigure"

echo "INSTALL UPSTART CONF"
echo "START UPSTART JOB"
