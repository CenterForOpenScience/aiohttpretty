.PHONY: format
format:
	black --line-length 79 aiohttpretty tests
	isort --profile black --line-length 79 aiohttpretty tests

.PHONY: test
test:
	pytest tests
