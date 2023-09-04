.PHONY: run clean setup linux

clean:
	rm -rf __pycache__ dist

run:
	python3 main.py

setup:
	pip3 install -r requirements.txt

linux:
	python3 build.py