# oh-my-deepseek-harness test channels (QA-001 / FR-QA-001,004-006,008-009)
# - test-fast:       no network / real HOME / API. Pure unit & contract tests.
# - test-integration: controlled processes/artifacts (server E2E, install, lifecycle).
# - test-release:    final matrix + evidence + known-defect gate.
PYTHON ?= python

.PHONY: test test-fast test-integration test-release

test: test-fast test-integration test-release
	@echo "all QA channels passed"

test-fast:
	@bash scripts/test_fast.sh "$(PYTHON)"

test-integration:
	@bash scripts/test_integration.sh "$(PYTHON)"

test-release:
	@bash scripts/test_release.sh "$(PYTHON)"