"""Reaktor models that use barrel for encapsulation."""
from setuptools import setup, find_packages


setup(
    name='barrel-reaktor',
    version='0.0.1-dev',
    description='python interface to reaktor API',
    long_description=__doc__,
    license='BSD',
    author='txtr web team',
    author_email='web-dev@txtr.com',
    url='https://github.com/txtr/barrel-reaktor/',
    packages=find_packages(),
    platforms='any',
    install_requires=['barrel==0.0.1-dev', ],
    dependency_links=[
        'https://github.com/txtr/barrel/zipball/master#egg=barrel-0.0.1-dev',
        'https://github.com/txtr/python-money/zipball/master#egg=python-money',
    ]
)
