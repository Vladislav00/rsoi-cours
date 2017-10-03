#!/bin/bash

sudo apt-get install sqlite3
d="$(pwd)"
data="$(locate redis-cli)"
if [[ $data == '' ]]; then
	sudo apt-get update
	sudo apt-get install build-essential tcl
	cd /tmp
	curl -O http://download.redis.io/redis-stable.tar.gz
	tar xzvf redis-stable.tar.gz
	cd redis-stable
	make
	sudo make install
	sudo mkdir /etc/redis
	sudo cp "$d/redis.conf" /etc/redis/redis.conf
	sudo cp "$d/redis.service" /etc/systemd/system/redis.service
	sudo systemctl enable redis
	sudo systemctl start redis
	cd "$d"
fi 
sudo apt-get install nginx
sudo ln -s rsoikurs_nginx.conf /etc/nginx/sites-enabled/rsoikurs_nginx.conf
sudo nginx -s reload
sudo apt-get install python3
sudo pip3 install uwsgi

python3 -m venv agregator/env
cd agregator
source env/bin/activate
pip install -r requirements.txt
deactivate
cd ..

python3 -m venv auth/env
cd auth
source env/bin/activate
pip install -r requirements.txt
./manage.py migrate
./manage.py createservicetoken
cred="$(./manage.py initsuperuser)"
deactivate
cd ..
cp auth/service_credentials.txt agregator/service_credentials.txt

python3 -m venv bonuscodes/env
cd bonuscodes
source env/bin/activate
pip install -r requirements.txt
deactivate
cd ..

python3 -m venv economics/env
cd economics
source env/bin/activate
pip install -r requirements.txt
deactivate
cd ..

python3 -m venv prizes/env
cd prizes
source env/bin/activate
pip install -r requirements.txt
./manage.py migrate
deactivate
cd ..

echo "chdir = $d/agregator" >> uwsgi/vassals/aggregator_uwsgi.ini 
echo "home = $d/agregator/env" >> uwsgi/vassals/aggregator_uwsgi.ini 

echo "chdir = $d/auth" >> uwsgi/vassals/auth_uwsgi.ini 
echo "home = $d/auth/env" >> uwsgi/vassals/auth_uwsgi.ini 

echo "chdir = $d/bonuscodes" >> uwsgi/vassals/bonuscodes_uwsgi.ini 
echo "home = $d/bonuscodes/env" >> uwsgi/vassals/bonuscodes_uwsgi.ini 

echo "chdir = $d/economics" >> uwsgi/vassals/economics_uwsgi.ini 
echo "home = $d/economics/env" >> uwsgi/vassals/economics_uwsgi.ini 

echo "chdir = $d/prizes" >> uwsgi/vassals/prizes_uwsgi.ini 
echo "home = $d/prizes/env" >> uwsgi/vassals/prizes_uwsgi.ini 


echo $cred
