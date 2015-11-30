# -*- coding: utf-8 -*-
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name='allegro',
    version='0.1',
    description='',
    author="Joe D'Andrea",
    author_email='jdandrea@research.att.com',
    install_requires=[
        "pecan",
        "pecan-notario",
        "sqlalchemy",
    ],
    test_suite='allegro',
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(exclude=['ez_setup']),
    entry_points="""
        [pecan.command]
        populate=allegro.commands.populate:PopulateCommand
    """
)
