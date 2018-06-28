import setuptools

with open('README.rst', 'r') as fh:
    long_description = fh.read()


requires = [
    'requests>=2.14.0'
]

setuptools.setup(
    name='coinbasepro',
    version='0.0.1',
    description='A Python interface for the Coinbase Pro API.',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author='Alex Contryman',
    author_email='acontry@gmail.com',
    url='https://github.com/acontry/coinbasepro',
    packages=setuptools.find_packages(),
    python_requires='>=3.4.x',
    install_requires=requires,
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3'
    ),
)
