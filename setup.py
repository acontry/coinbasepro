import setuptools

with open("README.rst", "r") as fh:
    readme = fh.read()

with open("HISTORY.rst", "r") as f:
    history = f.read()


requires = ["requests>=2.20.0"]

setuptools.setup(
    name="coinbasepro",
    version="0.4.1",
    description="A Python interface for the Coinbase Pro/Coinbase Exchange API.",
    long_description=readme + "\n\n" + history,
    long_description_content_type="text/x-rst",
    license="MIT",
    author="Alex Contryman",
    author_email="acontry@gmail.com",
    url="https://github.com/acontry/coinbasepro",
    packages=setuptools.find_packages(),
    python_requires=">=3.4",
    install_requires=requires,
    extras_require={
        "dev": [
            "pip-tools",
            "pre-commit",
            "pygments",  # Pycharm readme rendering workaround
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
