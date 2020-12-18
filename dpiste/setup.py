# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

setup(
    name='deep-piste',
    version='0.0.2',
    description='Evaluating the impact of IA on Breast Cancer Screening Program',
    long_description=readme,
    long_description_content_type='text/markdown',
    author='Francisco Orchard',
    author_email='f.orchard@epiconcept.fr',
    url='https://github.com/Epiconcept-Paris/deep.piste',
    license="GNU General Public License v2.0",
    install_requires=[
      "kskit"
    ],
    packages=find_packages(exclude=('tests', 'docs'))
)

