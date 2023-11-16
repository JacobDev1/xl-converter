.PHONY: run clean build build-appimage build-7z

clean:
	rm -rf dist

clean-all: clean
	rm -rf build __pycache__

run:
	python3 main.py

build:
	python3 build.py

build-appimage:
	python3 build.py -a

build-7z:
	python3 build.py -p