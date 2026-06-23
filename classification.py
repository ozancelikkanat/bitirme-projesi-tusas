[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "wrinkle-life-risk"
version = "1.0.0"
description = "Academic decision-support model for CFRP wrinkle risk prioritization."
requires-python = ">=3.10"
dependencies = [
  "pandas>=2.0",
  "numpy>=1.24",
  "matplotlib>=3.7",
]

[project.optional-dependencies]
app = ["streamlit>=1.32", "openpyxl>=3.1", "xlrd>=2.0"]
test = ["pytest>=7.4"]

[tool.pytest.ini_options]
testpaths = ["tests"]
