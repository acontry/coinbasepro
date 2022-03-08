.PHONY: install-requirements
install-requirements:
	pip-sync

.PHONY: requirements
requirements:
	export CUSTOM_COMPILE_COMMAND="make requirements"; pip-compile --extra dev --upgrade

.PHONY: publish
publish:
	pip install 'twine>=1.5.0'
	python setup.py sdist bdist_wheel
	twine upload dist/*
	rm -rf build dist .egg coinbasepro.egg-info
