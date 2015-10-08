docs:
	python setup.py upload_docs --upload-dir docs/_build/html

install:
	sudo python setup.py install --user
	sudo -H python setup.py install --user
	sudo python setup.py install
	sudo -H python setup.py install

update:
	python setup.py sdist upload --sign
	sudo -H pip install hwrt --upgrade

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