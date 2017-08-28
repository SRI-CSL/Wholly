
all:
	@echo ''
	@echo 'Here are the targets:'
	@echo ''
	@echo 'To develop          :    "make develop"'
	@echo 'To install          :    "make install"'
	@echo 'To publish          :    "make publish"'
	@echo 'To pylint           :    "make lint"'
	@echo 'To clean            :    "make clean"'

	@echo ''

#local editable install for developing
develop:
	pip install -e .


dist: clean
	python setup.py bdist_wheel

# If you need to push this project again,
# INCREASE the version number in wholly/version.py,
# otherwise the server will give you an error.

publish: dist
	python setup.py sdist upload

install:
	pip install



clean:
	rm -rf build dist wholly.egg-info wholly/*.pyc


PYLINT = $(shell which pylint)

lint:
ifeq ($(PYLINT),)
	$(error lint target requires pylint)
endif
#	@ $(PYLINT) -E *.py
# for detecting more than just errors:
	@ $(PYLINT) --rcfile=.pylintrc wholly/*.py
