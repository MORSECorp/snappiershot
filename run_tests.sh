#!/usr/bin/env bash
# Script for running all tests and reporting coverage.
# Run from project root.

set -e

coverage run --source=snappiershot -m pytest --quiet && coverage report
