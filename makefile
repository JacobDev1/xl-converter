.PHONY: run clean setup build

clean:
	rm -rf __pycache__ dist

run:
	python3 main.py

setup:
	pip3 install -r requirements.txt

build:
	python3 build.py