#!/usr/bin/env python3
"""
Setup script for ai_manager package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

from wl_version_manager import VersionManager

setup(
    name="wl_ai_manager",
    version=VersionManager.get_version(),
    description="Python module providing unified access to OpenAI's chat, text-to-speech, and transcription APIs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Chris Watkins",
    author_email="chris@watkinslabs.com",
    url="https://github.com/watkinslabs/ai_manager",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "openai>=1.0.0",
        "soundfile>=0.12.0",
        "requests>=2.25.0",
        "jsonschema",
        "replicate",
        "soundfile",
        "pillow"
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=22.0",
            "flake8>=4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            # Add CLI scripts here if needed
        ],
    },
    include_package_data=True,
    zip_safe=False,
)