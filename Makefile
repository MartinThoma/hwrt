docs:
	python setup.py upload_docs --upload-dir docs/_build/html

update:
	python setup.py sdist upload
	sudo pip install hwrt --upgrade

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