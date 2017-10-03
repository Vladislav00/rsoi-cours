#!/bin/bash

inotifywait -r -m ./  -e moved_to -e close_write|
while read -r directory events filename; do
	if [[ $filename =~ .*\.py$ ]] ; then
		if [[ $directory =~ \./agregator ]] ; then
			touch uwsgi/vassals/aggregator_uwsgi.ini
		fi
		if [[ $directory =~ \./auth ]] ; then
			touch uwsgi/vassals/auth_uwsgi.ini
		fi
		if [[ $directory =~ \./bonuscodes ]] ; then
			touch uwsgi/vassals/bonuscodes_uwsgi.ini
		fi
		if [[ $directory =~ \./economics ]] ; then
			touch uwsgi/vassals/economics_uwsgi.ini
		fi
		if [[ $directory =~ \./prizes ]] ; then
			touch uwsgi/vassals/prizes_uwsgi.ini
		fi
	fi	
done
