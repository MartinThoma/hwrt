docs:
	python setup.py upload_docs --upload-dir docs/_build/html

install:
	pip install -e . --user

upload:
	make clean
	python setup.py sdist bdist_wheel && twine upload dist/*

test:
	pytest

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
	rm -rf .tox
	python setup.py clean --all
	rm -f *.hdf5 *.yml *.csv
	find . -name "*.pyc" -exec rm -rf {} \;
	find . -type d -name "__pycache__" -delete
	rm -rf build
	rm -rf cover
	rm -rf dist
	rm -rf hwrt.egg-info
	rm -rf tests/reports
