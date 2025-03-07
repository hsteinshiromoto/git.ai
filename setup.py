#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="git-ai",
    version="0.1.0",
    author="Git AI Contributors",
    author_email="",
    description="A tool for summarizing git repository history",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/git-ai",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov",
        ]
    },
    entry_points={
        "console_scripts": [
            "git-ai=src.git_summarizer:main",
        ],
    },
)