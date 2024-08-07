PYTHON 				= python
ENV_BUILD 			= ./env_build
ENV_DEV 			= ./env_dev
REQUIREMENTS_BUILD 	= requirements.txt
REQUIREMENTS_TEST 	= requirements_test.txt

.PHONY: clean
clean:
	rm -rf dist

.PHONY: clean-all
clean-all: clean
	rm -rf build __pycache__

.PHONY: src
src: clean
	mkdir -p dist/src
	
	cp .gitignore .rsync-exclude
	sed -i '/^\/bin\//d; /^\/misc\//d' .rsync-exclude
	rsync -a --exclude-from=.rsync-exclude --exclude=.git --exclude=screenshots ./ dist/src/
	rm .rsync-exclude

	cd dist && 7z a src_`date +%Y%m%d_%H%M%S`.zip src/

.PHONY: test-slowest
test-slowest:
	export PYTHONPATH=$$PYTHONPATH:. && pytest --durations=10 --durations-min=0.02 tests/

.PHONY: test-no-cache
test-no-cache:
	export PYTHONPATH=$$PYTHONPATH:. && pytest --cache-clear tests/

.PHONY: test-old
test-old:
	@if [ -n "$(name)" ]; then \
		$(PYTHON) -m unittest test_old.TestMainWindow.$(name); \
	else \
		$(PYTHON) test_old.py; \
	fi

.PHONY: coverage
coverage:
	export PYTHONPATH=$$PYTHONPATH:. && pytest --cov=core --cov=ui --cov=main --cov=data --cov=build --cov-report term-missing tests/
	coverage html

.PHONY: venv-build
venv-build:
	@if [ -d $(ENV_BUILD) ] ; then \
		echo "venv-build already exists"; \
	else \
		echo "Creating venv-build..."; \
		$(PYTHON) -m venv $(ENV_BUILD); \
		$(ENV_BUILD)/bin/python3 -m pip install --upgrade pip; \
		$(ENV_BUILD)/bin/python3 -m pip install -r $(REQUIREMENTS_BUILD); \
		echo "venv-build has been created at $(ENV_BUILD)"; \
	fi

.PHONY: venv-dev
venv-dev:
	@if [ -d $(ENV_DEV) ] ; then \
		echo "venv-dev already exists"; \
	else \
		echo "Creating venv-dev..."; \
		$(PYTHON) -m venv $(ENV_DEV); \
		$(ENV_DEV)/bin/python3 -m pip install --upgrade pip; \
		$(ENV_DEV)/bin/python3 -m pip install -r $(REQUIREMENTS_BUILD); \
		$(ENV_DEV)/bin/python3 -m pip install -r $(REQUIREMENTS_TEST); \
		echo "venv-build has been created at $(ENV_DEV)"; \
	fi