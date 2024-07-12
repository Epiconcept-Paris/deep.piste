# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md', encoding="utf-8") as f:
    readme = f.read()

setup(
    name='deep-piste',
    version='0.0.18',
    description='Evaluating the impact of IA on Breast Cancer Screening Program',
    long_description=readme,
    long_description_content_type='text/markdown',
    author=['Francisco Orchard', 'William Madié'],
    author_email=['f.orchard@epiconcept.fr', 'w.madie@epiconcept.fr'],
    url='https://github.com/Epiconcept-Paris/deep.piste',
    license="GNU General Public License v2.0",
    install_requires=[
        "deidcm",
        "pycryptodome ",
        "qrcode",
        "pyzbar[scripts]",
        "requests",
        "pynetdicom",
        "xmltodict",
        "clipboard",
        "pyarrow",
        "ipykernel",
        "nbconvert",
        "jupytext",
        "plotly",
        "python-gnupg",
        "fabric",
        "paramiko"
    ],
    packages=find_packages(),
    include_package_data=True,
    extras_require={
        "quality-tools": [
            "pylint",
            "autopep8",
            "pytest",
            "coverage"
        ]
    }
)
