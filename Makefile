.PHONY: docs, test

init:
	pip install -r requirements.txt

test:
	python -m unittest discover -t .

docs: init
	pdoc --html --html-dir docs vt102 --overwrite

update-docs: docs
	ghp-import -n -p docs/vt102

publish:
	python setup.py register
	python setup.py sdist upload
