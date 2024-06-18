.PHONY: run clean src-full src-min test test-old coverage test-slowest test-no-cache

clean:
	rm -rf dist

clean-all: clean
	rm -rf build __pycache__

run:
	python3 main.py

src: clean
	mkdir -p dist/src
	
	cp .gitignore .rsync-exclude
	sed -i '/^\/bin\//d; /^\/misc\//d' .rsync-exclude
	rsync -a --exclude-from=.rsync-exclude --exclude=.git --exclude=screenshots ./ dist/src/
	rm .rsync-exclude

	cd dist && 7z a src_`date +%Y%m%d_%H%M%S`.zip src/

test:
	python3 test.py

test-slowest:
	export PYTHONPATH=$$PYTHONPATH:. && pytest --durations=10 --durations-min=0.02 tests/

test-no-cache:
	export PYTHONPATH=$$PYTHONPATH:. && pytest --cache-clear tests/

test-old:
	@if [ -n "$(name)" ]; then \
		python -m unittest test_old.TestMainWindow.$(name); \
	else \
		python test_old.py; \
	fi

coverage:
	export PYTHONPATH=$$PYTHONPATH:. && pytest --cov=core --cov=ui --cov=main --cov=data --cov=build --cov-report term-missing tests/
	coverage html