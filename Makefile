docs:
	python setup.py upload_docs --upload-dir docs/_build/html

install:
	pip install -e . --user

upload:
	make clean
	python3 setup.py sdist bdist_wheel && twine upload dist/*

test:
	nosetests --with-coverage --cover-erase --cover-package hwrt --logging-level=INFO --cover-html

testall:
	make test
	cheesecake_index -n hwrt -v

count:
	cloc . --exclude-dir=docs,cover,dist,hwrt.egg-info

countc:
	cloc . --exclude-dir=docs,cover,dist,hwrt.egg-info,tests

countt:
	cloc tests

clean:
	rm -f *.hdf5 *.yml *.csv
	find . -name "*.pyc" -exec rm -rf {} \;
	find . -type d -name "__pycache__" -delete
	sudo rm -rf build
	sudo rm -rf cover
	sudo rm -rf dist
	sudo rm -rf hwrt.egg-info
