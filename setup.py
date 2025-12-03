#!/usr/bin/env python3
"""
Setup script for the Triones LED Controller Python module
"""

from setuptools import setup, find_packages
import os

# Read the README file for the long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Python module for controlling Triones RGBW Bluetooth LED controllers"

# Read requirements from requirements.txt
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return ['bleak>=0.21.0']

setup(
    name="bleak-triones-controller",
    version="1.0.0",
    author="User",
    author_email="user@example.com",
    description="Python module for controlling Triones RGBW Bluetooth LED controllers",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/sessions-matthew/bleak-triones-controller",
    py_modules=["triones"],
    packages=["examples"],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Home Automation",
        "Topic :: System :: Hardware",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="bluetooth ble led rgb rgbw triones lighting smart-home automation",
    project_urls={
        "Bug Reports": "https://github.com/sessions-matthew/bleak-triones-controller/issues",
        "Source": "https://github.com/sessions-matthew/bleak-triones-controller",
        "Documentation": "https://github.com/sessions-matthew/bleak-triones-controller/blob/main/README.md",
    },
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-asyncio>=0.18.0',
            'black>=22.0.0',
            'flake8>=4.0.0',
            'mypy>=0.910',
        ],
    },
    entry_points={
        'console_scripts': [
            'triones-demo=examples.demo:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)