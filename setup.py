import os
from setuptools import find_packages, setup

version_file = os.path.join('damster', 'VERSION')


setup(
    name='damster',
    description='Reports and metrics for Atlassian Tools',
    long_description=open('README.md', 'r').read(),
    license='Apache License 2.0',
    version=open(version_file, 'r').read().strip(),
    download_url='https://github.com/cattz/damster',

    author='Xabier Davila',
    author_email='davila.xabier@gmail.com',

    packages=find_packages(),
    package_dir={'damster': 'damster'},
    include_package_data=True,

    zip_safe=False,

    install_requires=[
        'configparser',
        'arrow',
        'click',
        'atlassian-python-api',
        'arrow',
        'influxdb',
        'schedule',
        'jinja2',
        'psycopg2',
        'sshtunnel',
        'six'
    ],

    extras_require={
        'dev': [
            'pytest',
            'pytest-pep8',
            'coverage',
            'tox'
        ],
    },
    platforms='Platform Independent',

    entry_points={
        "console_scripts": [
            "damster    = damster.cli:cli",
        ]
    },

    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Libraries :: Application Frameworks'
    ]
)
