from setuptools import find_packages, setup


setup(
    name='pyrfidsim',
    version='1.0.0',
    author='Vilmen Abramian',
    author_email='abramian.vl@phystech.edu',
    platforms=['any'],
    license='MIT',
    url='https://github.com/VilmenAbramian/simulation',
    packages=['pysim'],
    install_requires=[
        'click',
        'colorama',
        'pydantic',
    ],
    test_requires=[
        'pytest',
    ],
    entry_points='''
        [console_scripts]
        sim=pysim.main:cli
    ''',
)
