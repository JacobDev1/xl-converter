.PHONY: run clean build

clean:
	rm -rf dist

clean-all: clean
	rm -rf build __pycache__

run:
	python3 main.py

build:
	python3 build.py