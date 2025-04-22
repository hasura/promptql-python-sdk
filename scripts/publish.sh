#!/bin/bash
set -e

# Clean up previous builds
rm -rf dist/
rm -rf build/
rm -rf *.egg-info

# Build the package
poetry build

# Check the package
poetry run twine check dist/*

# Upload to PyPI (uncomment when ready)
# poetry publish

echo "Package built successfully. To publish to PyPI, run: poetry publish"
