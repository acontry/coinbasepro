init:
	pip install pipenv --upgrade
	pipenv install --dev --skip-lock

publish:
	pip install 'twine>=1.5.0'
	python setup.py sdist bdist_wheel
	twine upload dist/*
	rm -rf build dist .egg coinbasepro.egg-info

.PHONY: init publish
