package:
	conda env create -f env.yml --force;\
  echo ;\
  if [ $${CONDA_DEFAULT_ENV:-x} != deep.piste ];\
    then \
      echo "Please activate environment and repeat";\
    else \
      echo "Using environment $$CONDA_DEFAULT_ENV";\
      pip install -e ../kskit;\
   fi
importesis:
	python -i testEsis.py `pass epitools/neoesis.preprod.voozanoo.net/neodemat/f.orchard` 20286
connectdb:
	~/sessions/mysql.sh bdd-preprod neoesis_preprod4 neoesis_preprod4	
test:
	nosetests tests
