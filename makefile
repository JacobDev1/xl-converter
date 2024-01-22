.PHONY: run clean build build-appimage build-7z src-full src-min test

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

src-full: clean
	mkdir -p dist/src
	rsync -a --exclude-from=.gitignore ./ dist/src/

src-min: clean
	mkdir -p dist/src
	rsync -a --include=misc/* --exclude-from=.gitignore --exclude=.git --exclude=screenshots --exclude=.github --exclude=.pytest_cache ./ dist/src/

src: src-min

src-zip: src
	cd dist && 7z a src_`date +%Y%m%d_%H%M%S`.zip src/

test:
ifdef n
	python3 -m unittest tests.TestMainWindow.$(n)
else
	python3 tests.py
endif