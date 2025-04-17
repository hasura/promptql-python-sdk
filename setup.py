"""
Setup script for the promptql-api-sdk package.
"""

from setuptools import setup, find_packages

setup(
    name="promptql-api-sdk",
    version="0.1.0",
    description="Python SDK for PromptQL Natural Language API",
    author="Hasura SDK Team",
    author_email="info@hasura.io",
    url="https://github.com/hasura/promptql-api-sdk",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "pydantic>=2.0.0",
        "typing-extensions>=4.0.0",
    ],
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
