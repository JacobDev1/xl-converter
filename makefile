.PHONY: run clean build

clean:
	rm -rf __pycache__ dist

run:
	python3 main.py

build:
	python3 build.py