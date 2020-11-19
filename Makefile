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

test:
	nosetests tests
