from setuptools import find_packages, setup


setup(
    name='pyrfidsim',
    version='1.0.0',
    author='Vilmen Abramian',
    author_email='vilmen.abramian@gmail.com',
    platforms=['any'],
    license='MIT',
    url='https://github.com/VilmenAbramian/simulation',
    packages=['pysim'],
    install_requires=[
        'click==8.1.7',
        'colorama==0.4.6',
        'pydantic==2.11.4',
        'numpy==2.2.5',
        'matplotlib==3.10.1',
        'scipy==1.15.2',
        'tabulate==0.9.0',
    ],
    test_requires=[
        'pytest',
    ],
    entry_points='''
        [console_scripts]
        sim=pysim.main:cli
    ''',
)
