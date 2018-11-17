#!/usr/bin/env python
# -*- coding:utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='parade',
    version='0.1.22.1',
    description='A ETL engine for pandas-based data task',
    author='He Bai',
    author_email='bailaohe@gmail.com',
    packages=find_packages('src'),
    package_dir=({'parade': 'src/parade'}),
    zip_safe=False,
    include_package_data=True,
    package_data={'': ['*.json', '*.xml', '*.yml', '*.tpl']},
    install_requires=['pandas', 'sqlalchemy', 'requests', 'pyyaml', 'flask',
                      'flask_cors', 'flask_restful', 'psycopg2', 'mysqlclient', 'xlsxwriter',
                      'PyGithub', 'pymongo', 'Flask-SocketIO', 'redis', 'jupyter', 'nbformat'],
    entry_points={
        'console_scripts': [
            'parade = parade.cmdline:execute',
        ],
    },
    url='https://github.com/bailaohe/parade',
    download_url='https://github.com/bailaohe/parade/tarball/0.1',
)
