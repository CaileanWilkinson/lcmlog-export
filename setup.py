from setuptools import *
with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    # Metadata
    name="lcm-export",
    version="1.0.1",
    author="Cailean Wilkinson",
    author_email="cailean.wilkinson@gmail.com",
    description="Exports lcm log files to Matlab .mat and Python pickle .pkl files.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="LGPL-3.0",
    url="https://github.com/CaileanWilkinson/lcmlog-export",
    python_requires='>=3.6',
    # Automatically detect python files
    packages=find_packages(),

    # Install `lcm-export` to /usr/local/bin as a binary script
    entry_points={
        'console_scripts': [
            'lcm-export=lcm_export.lcmlog_export:main',
        ],
    }
)
