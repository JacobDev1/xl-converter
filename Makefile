SHELL               := bash
PYTHON              := python
ENV_BUILD           := ./env_build
ENV_DEV             := ./env_dev
REQUIREMENTS_BUILD  := requirements.txt
REQUIREMENTS_TEST   := requirements_test.txt
BIN_DIR             := bin
SCRIPT_DIR          := misc/build_scripts

# Detect host OS
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
  PLAT ?= linux
else ifeq ($(UNAME_S),Darwin)
  PLAT ?= macos
else ifneq (,$(MSYSTEM))
	ifneq ($(MSYSTEM),MINGW64)
	  $(error Please run this Makefile in a MINGW64 shell. Current shell: $(MSYSTEM))
	endif
	PLAT ?= win
else ifneq (,$(findstring CYGWIN,$(UNAME_S)))
  PLAT ?= win
else
  PLAT ?= linux
endif

# Tool list
TOOLS := libjxl libavif imagemagick libjpeg-turbo oxipng

# Tool layout
bin_dir_linux := $(BIN_DIR)/linux
bin_dir_win   := $(BIN_DIR)/win
bin_dir_macos := $(BIN_DIR)/macos

bins_linux_libjxl        := cjxl djxl jxlinfo cjpegli
dest_linux_libjxl        :=
bins_linux_libavif       := avifenc avifdec
dest_linux_libavif       :=
bins_linux_imagemagick   :=
dest_linux_imagemagick   := imagemagick
bins_linux_libjpeg-turbo := jpegtran
dest_linux_libjpeg-turbo :=
bins_linux_oxipng        := oxipng
dest_linux_oxipng        :=

bins_win_libjxl          :=
dest_win_libjxl          := libjxl
bins_win_libavif         :=
dest_win_libavif         := libavif
bins_win_imagemagick     :=
dest_win_imagemagick     := imagemagick
bins_win_libjpeg-turbo   := jpegtran
dest_win_libjpeg-turbo   :=
bins_win_oxipng          :=
dest_win_oxipng          := oxipng

bins_macos_libjxl        := cjxl djxl jxlinfo cjpegli
dest_macos_libjxl        :=
bins_macos_libavif       :=
dest_macos_libavif       := libavif
bins_macos_imagemagick   :=
dest_macos_imagemagick   := imagemagick
bins_macos_libjpeg-turbo := jpegtran
dest_macos_libjpeg-turbo :=
bins_macos_oxipng        :=
dest_macos_oxipng        := oxipng

# Help
.PHONY: help
help:
	@echo "Usage: make <tool> [PLAT=linux|win|macos]"
	@echo "    tools: $(TOOLS)"
	@echo "    other: deps build build-all"

# Usage: docker_build <Dockerfile> <src> <dst>
define docker_build
	mkdir -p $(3)
	docker build -f $(1) --progress=plain --iidfile tmp.txt . && \
	image_id=$$(cat tmp.txt) && \
	container_id=$$(docker create $${image_id}) && \
	docker cp $${container_id}:$(2) $(3) && \
	docker rm $${container_id} && \
	docker rmi -f $${image_id}
	rm tmp.txt
endef

.PHONY: $(TOOLS)
$(TOOLS): %: build-%-$(PLAT)

.PHONY: deps
deps: $(TOOLS)
ifeq ($(PLAT),win)
	deps += build-exiftool-win
endif
# ifeq ($(PLAT),macos)
# 	deps += build-exiftool-macos
# endif

.PHONY: build
build: build-$(PLAT)

.PHONY: build-linux
build-linux:
	rm -rf dist
	$(call docker_build,$(SCRIPT_DIR)/linux/Dockerfile.build,/export/.,dist)

.PHONY: build-win
build-win:
	@echo "Cannot call from MSYS2 to avoid runtime mismatch when bundling. Open CMD and run:"
	@echo "python misc\build_scripts\windows\build.py"

.PHONY: build-macos
build-macos:
	rm -rf dist
	bash $(SCRIPT_DIR)/macos/build.sh

.PHONY: build-all
build-all: deps build

define build_cleanup
	@rm -rf \
		$(addprefix $(bin_dir_$(PLAT))/, $(bins_$(PLAT)_$(1))) \
		$(if $(dest_$(PLAT)_$(1)),\
			$(bin_dir_$(PLAT))/$(dest_$(PLAT)_$(1)))
endef

.PHONY: build-%-win
build-%-win:
	@echo "Building $*"
	$(call build_cleanup,$*)
	bash $(SCRIPT_DIR)/windows/$*.sh

.PHONY: build-%-linux
build-%-linux:
	@echo "Building $*"
	$(call build_cleanup,$*)
	$(call docker_build,$(SCRIPT_DIR)/linux/Dockerfile.$*,/src/bin/.,$(bin_dir_linux)$(if $(dest_linux_$*),/$(dest_linux_$*),))

.PHONY: build-%-macos
build-%-macos:
	@echo "Building $*"
	$(call build_cleanup,$*)
	bash $(SCRIPT_DIR)/macos/$*.sh

.PHONY: exiftool
ifeq ($(PLAT),win)
exiftool:
	@rm -rf ./bin/win/exiftool
	bash $(SCRIPT_DIR)/windows/exiftool.sh
else ifeq ($(PLAT),macos)
exiftool:
	@rm -rf ./bin/macos/exiftool
	bash $(SCRIPT_DIR)/macos/exiftool.sh
else
exiftool:
	$(error The 'exiftool' target is only available on Windows and macOS)
endif

# Misc.

.PHONY: clean
clean:
	rm -rf _pyinstaller __pycache__ htmlcov .coverage .pytest_cache

.PHONY: src
src:
	rm -rf ./dist
	mkdir -p dist/src
	
	cp .gitignore .rsync-exclude
	sed -i '/^\/bin\//d; /^\/misc\//d' .rsync-exclude
	rsync -a --exclude-from=.rsync-exclude --exclude=.git --exclude=screenshots ./ dist/src/
	rm .rsync-exclude

	cd dist && 7z a -t7z -mx1 src_`date +%Y%m%d_%H%M%S`.7z src/
	rm -rf ./dist/src

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

# Testing

.PHONY: test
test:
	$(PYTHON) test.py

.PHONY: test-slowest
test-slowest:
	export PYTHONPATH=$$PYTHONPATH:. && pytest --durations=10 --durations-min=0.02 tests/

.PHONY: test-no-cache
test-no-cache:
	export PYTHONPATH=$$PYTHONPATH:. && pytest --cache-clear tests/

.PHONY: test-convert
test-convert:
	@if [ -n "$(name)" ]; then \
		QT_QPA_PLATFORM=offscreen xvfb-run -a $(PYTHON) -m unittest test_convert.TestMainWindow.$(name); \
	else \
		QT_QPA_PLATFORM=offscreen xvfb-run -a $(PYTHON) test_convert.py; \
	fi

.PHONY: coverage
coverage:
	export PYTHONPATH=$$PYTHONPATH:. && pytest --cov=core --cov=ui --cov=main --cov=data --cov=build --cov-report term-missing tests/
	coverage html

.PHONY: validate-appstream
validate-appstream:
	flatpak run --command=flatpak-builder-lint org.flatpak.Builder appstream ./misc/eu.codepoems.xl-converter.metainfo.xml
