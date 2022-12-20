from setuptools import find_packages, setup


setup(
    name="pyrfidsim",
    version="0.1.0",
    author="Andrey Larionov",
    author_email="larioandr@gmail.com",
    platforms=["any"],
    license="MIT",
    url="https://github.com/ipu64/pyrfidsim",
    packages=["pysim"],
    install_requires=[
        "click",
        "colorama",
        "pydantic",
    ],
    test_requires=[
        "pytest",
    ],
    entry_points='''
        [console_scripts]
        sim=pysim.main:cli
    ''',
)
