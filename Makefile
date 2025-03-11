# Makefile for running Python unit tests

.PHONY: test clean

test:
	python3 -m unittest discover -s src/tests -p "*_tests.py" -v

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
