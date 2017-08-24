
all:
	@echo ''
	@echo 'Here are the targets:'
	@echo ''
	@echo 'To pylint           :  "make lint"'
	@echo ''



PYLINT = $(shell which pylint)

lint:
ifeq ($(PYLINT),)
	$(error lint target requires pylint)
endif
#	@ $(PYLINT) -E *.py
# for detecting more than just errors:
	@ $(PYLINT) --rcfile=.pylintrc *.py
