#!/usr/bin/env bash
# Script for running all tests and reporting coverage.
set -e
coverage run --source=snappiershot -m pytest --quiet && coverage report
