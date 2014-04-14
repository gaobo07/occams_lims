import os
from subprocess import Popen, PIPE
from setuptools import setup, find_packages
import sys

HERE = os.path.abspath(os.path.dirname(__file__))

REQUIRES = [
    'alembic',
    'babel',
    'colander',
    'cssmin',
    'deform',
    'humanize',
    'jsmin',
    'lingua',
    'pyramid',
    'pyramid_chameleon',
    'pyramid_deform',
    'pyramid_layout',
    'pyramid_mailer',
    'pyramid_tm',
    'pyramid_redis_sessions',
    'pyramid_redis',
    'pyramid_rewrite',
    'pyramid_webassets',
    'pyramid_who',
    'reportlab',
    'SQLAlchemy',
    'six',
    'transaction',
    'webassets',
    'xlutils',
    'zope.sqlalchemy',
    'zope.dottedname',

    'occams.studies',
    'occams.datastore'
]

EXTRAS = {
    'postgresql': ['psycopg2'],
    'test': [
        'pyramid_debugtoolbar',
        'nose',
        'coverage',
        'WebTest',
        'beautifulsoup4'],
}


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

setup(
    name='occams.lab',
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
    url='https://bitbucket.org/ucsdbitcore/occams.lab',
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
    entry_points="""\
    [paste.app_factory]
    main = occams.lab:main
    """,
)
