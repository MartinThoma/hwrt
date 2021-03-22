docs:
	python setup.py upload_docs --upload-dir docs/_build/html

maint:
	pip install -r requirements/dev.txt
	pre-commit autoupdate && pre-commit run --all-files
	pip-compile -U setup.py -o requirements/prod.txt
	pip-compile -U requirements/ci.in
	pip-compile -U requirements/dev.in

upload:
	make clean
	python setup.py sdist bdist_wheel && twine upload dist/*

clean:
	python setup.py clean --all
	pyclean .
	rm -rf *.pyc build dist tests/reports docs/build .pytest_cache .tox .coverage html/
	rm -rf hwrt.egg-info
	rm -rf __pycache__ mpu/datastructures/trie/__pycache__ mpu/__pycache__ mpu/units/__pycache__ tests/__pycache__
	find . -name "*.pyc" -exec rm -rf {} \;
	find . -type d -name "__pycache__" -delete
	rm -f *.hdf5 *.yml *.csv

testall:
	make test
	cheesecake_index -n hwrt -v

count:
	cloc . --exclude-dir=docs,cover,dist,hwrt.egg-info

countc:
	cloc . --exclude-dir=docs,cover,dist,hwrt.egg-info,tests

countt:
	cloc tests
