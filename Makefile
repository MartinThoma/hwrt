docs:
	python setup.py upload_docs --upload-dir docs/_build/html

update:
	python setup.py sdist upload
	sudo pip install hwrt --upgrade

test:
	nosetests --with-coverage --cover-erase --cover-package hwrt --logging-level=INFO --cover-html