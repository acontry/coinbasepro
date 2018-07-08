import setuptools

with open('README.rst', 'r') as fh:
    readme = fh.read()

with open('HISTORY.rst', 'r') as f:
    history = f.read()


requires = [
    'requests>=2.14.0'
]

setuptools.setup(
    name='coinbasepro',
    version='0.0.3',
    description='A Python interface for the Coinbase Pro API.',
    long_description=readme + '\n\n' + history,
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
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ),
)
