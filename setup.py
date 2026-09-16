#!/usr/bin/env python3
"""
Setup script for omnipost-social-engine.
"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") if False else open("/dev/null") as f:
    long_description = ""

setup(
    name="omnipost-social-engine",
    version="1.0.0",
    description="Zero-dependency social media copywriting engine, thread splitter, campaign exporter, and Model Context Protocol (MCP) server.",
    long_description="Zero-dependency social media copywriting engine, thread splitter, campaign exporter, and Model Context Protocol (MCP) server.",
    long_description_content_type="text/markdown",
    author="Omnipost Contributors",
    license="MIT",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=[],
    extras_require={
        "dev": ["pytest>=7.0.0"],
    },
    entry_points={
        "console_scripts": [
            "omnipost=omnipost_social_engine.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
