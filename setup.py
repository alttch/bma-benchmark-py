__version__ = '0.0.6'

import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='bma_benchmark',
    version=__version__,
    author='Bohemia Automation / Altertech',
    author_email='div@altertech.com',
    description='Python benchmark tool',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/alttch/bma-benchmark-py',
    packages=setuptools.find_packages(),
    license='MIT',
    install_requires=['rapidtables>=0.1.11', 'neotermcolor>=2.0.8'],
    scripts=['bin/bma-benchmark'],
    classifiers=(
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Benchmark',
    ))
