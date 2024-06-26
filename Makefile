.EXPORT_ALL_VARIABLES:
SHELL = bash

init:
	if [ -d env ]; then\
	  rm -r env;\
	fi;
	if [ -f ${PYTHON} ]; then \
	  ${PYTHON} -m venv env; \
	else \
	  python3 -m venv env;\
	fi
	source  env/bin/activate; \
	python3 -m pip install --upgrade pip; \
	python3 -m pip install --upgrade setuptools wheel twine

install-dependencies:
	sudo apt install python3-tk;
	sudo apt install python3-venv;
	sudo apt install libzbar-dev

install:
	source env/bin/activate;\
	python3 -m pip install -e .;\
	python3 -m pip install -e ../deidcm\

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
	rm -f dist/*;\
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
