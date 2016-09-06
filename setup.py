import os
from subprocess import Popen, PIPE
from setuptools import setup, find_packages
from setuptools.command.develop import develop as _develop
import sys

HERE = os.path.abspath(os.path.dirname(__file__))

REQUIRES = [
    #
    # Package dependencies
    #
    # NOTE: If you edit these requirements, make sure you update the
    # requirements-develop.txt file
    #
    'alembic',
    'babel',
    'celery[redis]>=3.1,<3.1.99',
    'cssmin',
    'filemagic',
    'gevent',
    'gunicorn==19.3',
    'humanize',
    'jsmin',
    'lingua',
    'psycopg2',
    'python-dateutil',
    'python-slugify',
    'pyramid>=1.7',
    'pyramid_chameleon',
    'pyramid_exclog',
    'pyramid_tm',
    'pyramid_redis_sessions',
    'pyramid_redis',
    'pyramid_webassets',
    'pyramid_who',
    'reportlab',
    'repoze.who>=2.3.0',
    'six',
    'SQLAlchemy',
    'tabulate',
    'wtforms>=2.0.0',
    'wtforms-json',
    'wtforms-components',
    'zope.sqlalchemy',

    'occams',
    'occams_studies'
]

EXTRAS = {
    'test': [
        'sphinx',
        'sphinx-autobuild',
        'pyramid_debugtoolbar',
        'pytest',
        'pytest-cov',
        'fake-factory',
        'WebTest',
        'beautifulsoup4',
        'mock',
        'who_dev>=0.0.2',
    ]
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


class _custom_develop(_develop):
    def run(self):
        _develop.run(self)
        self.execute(_post_develop, [], msg="Running post-develop task")


def _post_develop():
    from subprocess import call
    call(['bower', 'install'], cwd=HERE)

setup(
    name='occams_lims',
    version=get_version(),
    description="Lab Inventory management",
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    keywords='',
    author='The YoungLabs',
    author_email='younglabs@ucsd.edu',
    url='https://github.com/younglabs/occams_lims',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=REQUIRES,
    extras_require=EXTRAS,
    tests_require=EXTRAS['test'],
    cmdclass={'develop': _custom_develop},
    entry_points="""\
    [console_scripts]
    """,
)
