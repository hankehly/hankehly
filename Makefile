build:
	python3 build.py

start: build
	python3 -m http.server 8000

.PHONY: build start
