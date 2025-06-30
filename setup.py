from setuptools import find_packages, setup

setup(
    name="pyrfidsim",
    version="1.1.0",
    author="Vilmen Abramian",
    author_email="vilmen.abramian@gmail.com",
    platforms=["any"],
    license="MIT",
    url="https://github.com/VilmenAbramian/simulation",
    packages=find_packages(include=["pysim", "pysim.*"]),
    install_requires=[
        "click==8.1.7",
        "colorama==0.4.6",
        "pydantic==2.11.4",
        "numpy==2.2.5",
        "matplotlib==3.10.1",  # Используется с PT Serif Caption (установить отдельно или через extras_require["fonts"])
        "scipy==1.15.2",
        "tabulate==0.9.0",
        "notebook",
        "ipykernel",
        "ipython",
        "plotly",
        "tqdm",
    ],
    tests_require=[
        "pytest",
    ],
    entry_points={
        "console_scripts": [
            "sim = pysim.main:cli",
        ],
    },
    python_requires=">=3.12",
    extras_require={
        "fonts": [
            "font-ttf-pt-serif-caption; sys_platform == 'linux'"
        ]
    }
)