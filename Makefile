CONFIG = config.txt

install:
	python3 -m pip install flake8 mypy build

run:
	python3 a_maze_ing.py $(CONFIG)

debug:
	python3 -m pdb a_maze_ing.py $(CONFIG)

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -name "*.pyc" -delete
	rm -rf build dist mazegen.egg-info

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict

test:
	python3 -m unittest discover -s tests

package:
	python3 -m build --outdir .

.PHONY: install run debug clean lint lint-strict test package
