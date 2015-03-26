import os
from subprocess import Popen, PIPE
from setuptools import setup, find_packages
from setuptools.command.develop import develop as _develop
import sys

HERE = os.path.abspath(os.path.dirname(__file__))

REQUIRES = [
    'alembic',                          # Database table upgrades
    'babel',                            # i18n
    'cssmin',                           # CSS asset compression
    'humanize',                         # human readable measurements
    'jsmin',                            # JS asset compression
    'lingua',                           # i18n
    'python-dateutil',                  # Date parsing
    'python-slugify',                   # path-friendly filenames
    'pyramid>=1.5',                     # Framework
    'pyramid_chameleon',                # Templating
    'pyramid_tm',                       # Centralized transations
    'pyramid_redis_sessions',           # HTTP session with redis backend
    'pyramid_rewrite',                  # Allows urls to end in "/"
    'pyramid_webassets',                # Asset management (ala grunt)
    'pyramid_who',                      # User authentication
    'six',                              # Py 2 & 3 compatibilty
    'SQLAlchemy>=0.9.0',                # Database ORM
    'tabulate',                         # ASCII tables for CLI pretty-print
    'wtforms',
    'wtforms-components',
    'wtforms-json',
    'zope.sqlalchemy',                  # Connects sqlalchemy to pyramid_tm

    'occams.datastore',                 # EAV
    'occams.accounts',
    'occams.studies'
]

EXTRAS = {
    'ldap': ['python3-ldap', 'who_ldap'],
    'sqlite': [],
    'postgresql': ['psycopg2', 'psycogreen'],
    'gunicorn': ['gunicorn'],
    'test': [
        'pyramid_debugtoolbar',
        'nose',
        'nose-testconfig',
        'coverage',
        'WebTest',
        'beautifulsoup4',
        'mock',
        'ddt'],
}


if sys.version_info < (2, 7):
    REQUIRES.extend(['argparse', 'ordereddict'])
    EXTRAS['test'].extend(['unittest2'])


if sys.version_info < (3, 0):
    REQUIRES.extend(['unicodecsv'])


def get_version():
    version_file = os.path.join(HERE, 'VERSION')

    # read fallback file
    try:
        with open(version_file, 'r+') as fp:
            version_txt = fp.read().strip()
    except:
        version_txt = None

    # read git version (if available)
    try:
        version_git = (
            Popen(['git', 'describe'], stdout=PIPE, stderr=PIPE, cwd=HERE)
            .communicate()[0]
            .strip()
            .decode(sys.getdefaultencoding()))
    except:
        version_git = None

    version = version_git or version_txt or '0.0.0'

    # update fallback file if necessary
    if version != version_txt:
        with open(version_file, 'w') as fp:
            fp.write(version)

    return version


class _custom_develop(_develop):
    def run(self):
        _develop.run(self)
        self.execute(_post_develop, [], msg="Running post-develop task")


def _post_develop():
    from subprocess import call
    call(['npm', 'install'], cwd=HERE)
    call(['./node_modules/.bin/bower', 'install'], cwd=HERE)

setup(
    name='occams.lims',
    version=get_version(),
    description="Lab Inventory management",
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    keywords='',
    author='BEAST Core Development Team',
    author_email='bitcore@ucsd.edu',
    url='https://bitbucket.org/ucsdbitcore/occams.lims',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'': 'src'},
    namespace_packages=['occams'],
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIRES,
    extras_require=EXTRAS,
    tests_require=EXTRAS['test'],
    test_suite='nose.collector',
    cmdclass={'develop': _custom_develop},
    entry_points="""\
    [paste.app_factory]
    main = occams.lims:main
    """,
)
