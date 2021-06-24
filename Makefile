SHELL = bash

init:
	
	if [ -f env ]; then\
	  rm -r env;\
	fi 
	python3 -m venv env;
	source env/bin/activate;
	pip install --upgrade pip;
	pip install --upgrade setuptools wheel twine

install-dependencies:
	sudo apt install python3-tk;
	sudo apt install python3-venv;
	sudo apt install libzbar-dev

install:
	source env/bin/activate;
	pip install -e .;
	pip install -e ../kskit

package:
	source env/bin/activate;\
	rm dist/*;\
	python setup.py sdist bdist_wheel

release-test:
	source env/bin/activate;\
	rm dist/*;\
	python setup.py sdist bdist_wheel;\
	python -m twine upload --repository testpypi dist/*

release:
	source env/bin/activate;\
	rm dist/*;\
	python setup.py sdist bdist_wheel;\
	python -m twine upload dist/*

check:
	source env/bin/activate;\
	rm dist/*;\
	python setup.py sdist bdist_wheel;\
	python -m twine check dist/*

importesis:
	python -i testEsis.py `pass epitools/neoesis.preprod.voozanoo.net/neodemat/f.orchard` 20286
connectdb:
	~/sessions/mysql.sh bdd-preprod neoesis_preprod4 neoesis_preprod4	
test:
	nosetests tests
