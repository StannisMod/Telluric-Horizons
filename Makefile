PYTHON ?= python3
.PHONY: build lint test package check-generated check-game
build:
	$(PYTHON) tools/build.py build
lint:
	$(PYTHON) tools/build.py lint
test:
	$(PYTHON) -m unittest discover -s tests -v
package:
	$(PYTHON) tools/build.py package
check-generated:
	$(PYTHON) tools/build.py check-generated
check-game:
	$(PYTHON) tools/build.py check-game
