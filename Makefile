# Makefile for brew-view

MODULE_NAME   = brew_view
PYTHON_TEST_DIR = test/unit
JS_DIR = brew_view/static

.PHONY: clean clean-build clean-test clean-pyc help test deps
.DEFAULT_GOAL := help
define BROWSER_PYSCRIPT
import os, webbrowser, sys
try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT
BROWSER := python -c "$$BROWSER_PYSCRIPT"


help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts
	$(MAKE) -C $(JS_DIR) clean


clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

lint: ## check style with flake8
	flake8 $(MODULE_NAME) $(PYTHON_TEST_DIR)

lint-all:
	$(MAKE) lint
	$(MAKE) -C $(JS_DIR) lint

test: ## run tests quickly with the default Python
	nosetests $(PYTHON_TEST_DIR)

test-all: ## run tests on every Python version with tox
	tox

coverage: ## check code coverage quickly with the default Python
	coverage run --source $(MODULE_NAME) -m nose test/unit/
	coverage report -m
	coverage html
	$(BROWSER) htmlcov/index.html

test-release: dist ## package and upload a release to the testpypi
	twine upload --repository testpypi dist/*

release: dist ## package and upload a release
	twine upload dist/*

dist: clean ## builds source and wheel package
	$(MAKE) -C $(JS_DIR) dist
	python setup.py sdist
	python setup.py bdist_wheel --universal
	ls -l dist

install: clean ## install the package to the active Python's site-packages
	python setup.py install

deps:
	pip install -r requirements.txt
	$(MAKE) -C $(JS_DIR) deps
