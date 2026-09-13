SHELL           := /usr/bin/bash

### ---------------------------------------------------
### Icons
### ---------------------------------------------------
ICONS_FOLDER	:= assets/icons
ICONS		+= simple/github simple/googlecolab simple/googleslides

### ---------------------------------------------------
### Make Documentation
### ---------------------------------------------------
HOST		:=
PORT		:=
localport	 = $(shell echo $$(( 1000 + ($$RANDOM % 9000) )))
ADDR		:= $(and $(or $(HOST),$(PORT)), $(or $(HOST),localhost):$(or $(PORT),$(localport)))
ADDR_SWITCH	:= $(and $(ADDR),-a $(ADDR))

PYTHONPATH	:= $${PYTHONPATH}:$${PWD}:$${PWD}/code

mkdocs		:= mkdocs

docserve :
	$(mkdocs) serve $(ADDR_SWITCH) --livereload

docbuild :
	$(mkdocs) build

docs : docserve

test :
	python -m unittest discover -s code/tests

run :
	python code/main.py

