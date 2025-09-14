.PHONY: lint test ci

lint:
	ruff .

test:
	bash scripts/run_tests.sh

ci: lint test
