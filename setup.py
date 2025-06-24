from setuptools import setup, find_packages
import os

# Lire le README
def read_readme():
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "NSM - Nexus Simple Memory"

setup(
    name="nsm",
    version="1.0.0",
    description="Nexus Simple Memory - Stockage compressé intelligent avec recherche sémantique",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="NSM Team",
    author_email="dev@nsm.com",
    url="https://github.com/Tryboy869/Nexus-Simple-Memory-",
    packages=find_packages(),
    install_requires=[
        "sentence-transformers>=2.2.0",
        "faiss-cpu>=1.7.0",
        "cryptography>=3.4.0",
        "brotli>=1.0.0",
        "zstandard>=0.15.0",
        "PyNaCl>=1.4.0",
        "click>=8.0.0",
        "numpy>=1.21.0",
        "scikit-learn>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
        "gpu": [
            "faiss-gpu>=1.7.0",
        ]
    },
    entry_points={
        'console_scripts': [
            'nsm=nsm.cli.main:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Archiving :: Compression",
        "Topic :: Text Processing :: Indexing",
    ],
    python_requires=">=3.8",
    keywords="compression, search, ai, nlp, storage, memory",
    project_urls={
        "Bug Reports": "https://github.com/Tryboy869/Nexus-Simple-Memory-/issues",
        "Source": "https://github.com/Tryboy869/Nexus-Simple-Memory-",
    },
)
