from setuptools import setup, find_packages

setup(
    name='c_import',
    packages=find_packages(),
    install_requires=[
        'clang',
        'hy',
    ]
)
