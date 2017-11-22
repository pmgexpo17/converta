import os
from setuptools import setup, find_packages
from setuptools.command.install import install

basePath = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(basePath, 'README.rst')) as f:
    README = f.read()


setup(name='converta',
      version=1.0,
      description='converta - v1 - csv to json conversion',
      long_description=README,
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Pylons",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application"
      ],
      keywords="web services",
      author='',
      author_email='',
      url='',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=['cornice', 'waitress','paste','cheroot'],
      entry_points="""\
      [paste.app_factory]
      main=converta:main
      """,)
