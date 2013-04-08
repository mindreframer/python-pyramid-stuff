INI = development.ini

project.egg-info:
	bin/python setup.py develop


.PHONY: run
run: project.egg-info
	bin/pserve --reload --monitor-restart $(INI)
