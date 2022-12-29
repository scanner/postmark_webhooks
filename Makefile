#
# Simple Makefile for inbound_api
#
MKFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
ROOT_DIR := $(realpath $(dir $(MKFILE_PATH)))

ACTIVATE := . $(ROOT_DIR)/venv/bin/activate &&
REQ_ACTIVATE := . $(ROOT_DIR)/venv_req/bin/activate &&

.git/hooks/pre-commit .git/hooks/pre-push:
	@$(ACTIVATE) pre-commit install
	@echo "pre-commit hooks installed!"
	@touch .git/hooks/pre-commit .git/hooks/pre-push

DEST_DIR := /var/tmp/postmark-api
PYTHON := python3.11
APP_FILES := $(wildcard $(ROOT_DIR)/app/*.py)
SCRIPT_FILES := $(wildcard $(ROOT_DIR)/scripts/*.sh)

clean::
	@rm -rf venv
	@rm -rf venv_*
	@find $(ROOT_DIR) -name \*~ -exec rm '{}' +
	@find $(ROOT_DIR) -name \*.pyc -exec rm '{}' +
	@find $(ROOT_DIR) -name __pycache__ -prune -exec rm -fr '{}' +
	@rm -rf build bdist cover dist sdist distribute-* *.egg *.egg-info
	@rm -rf node_modules
	@rm -rf *.tar.gz junit.xml coverage.xml .cache
	@rm -rf .tox .eggs .blackened .isorted
	@find $(ROOT_DIR) \( -name \*.orig -o -name \*.bak -o -name \*.rej \) -exec rm '{}' +

define venv_req
    @if [ ! -d $(ROOT_DIR)/venv_req ] ; then \
        $(PYTHON) -m venv $(ROOT_DIR)/venv_req ; \
	$(REQ_ACTIVATE) pip install -U pip ; \
	$(REQ_ACTIVATE) pip install pip-tools ; \
    fi
endef

$(ROOT_DIR)/venv: local.txt
	@if [ -d "$@" ] ; then \
	  $(ACTIVATE) pip-sync $(ROOT_DIR)/local.txt ; \
        else \
	  $(PYTHON) -m venv $@ ; \
	  $(ACTIVATE) pip install -U pip ; \
	  $(ACTIVATE) pip install -r $(ROOT_DIR)/local.txt ; \
        fi
	@touch $@

venv:: $(ROOT_DIR)/venv local.txt
venv:: .git/hooks/pre-commit
venv:: .git/hooks/pre-push

lint: venv
	@$(ACTIVATE) pre-commit run -a

install:
	mkdir -p "$(DEST_DIR)"
	mkdir -p "$(DEST_DIR)/app"
	mkdir -p "$(DEST_DIR)/scripts"
	install -m 644 "$(ROOT_DIR)/requirements.txt" "$(DEST_DIR)"
	install -m 644 $(APP_FILES) "$(DEST_DIR)/app/"
	install -m 755 $(SCRIPT_FILES) "$(DEST_DIR)/scripts"
	$(PYTHON) -m venv "$(DEST_DIR)/venv"
	cd "$(DEST_DIR)"
	. "$(DEST_DIR)/venv/bin/activate" && pip install -U pip
	. "$(DEST_DIR)/venv/bin/activate" && pip install -r "$(DEST_DIR)/requirements.txt"

run: venv
	$(ACTIVATE) uvicorn app.main:app --reload

test: venv
	$(ACTIVATE) pytest

requirements.txt: requirements.in
	@$(venv_req)
	@$(REQ_ACTIVATE) pip-compile $(ROOT_DIR)/requirements.in -o $(ROOT_DIR)/requirements.txt

local.txt: local.in requirements.in
	@$(venv_req)
	@$(REQ_ACTIVATE) pip-compile $(ROOT_DIR)/local.in -o $(ROOT_DIR)/local.txt

requirements: requirements.txt local.txt
