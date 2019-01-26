"""Setup for beautysh - A bash beautifier for the masses."""
from setuptools import setup
import sys


def get_version(file_name='beautysh/__init__.py'):
    """Get version info from __init__."""
    with open(file_name) as v_file:
        for line in v_file:
            if "__version__" in line:
                return eval(line.split('=')[-1])


if sys.version_info[0] < 3:
    with open("README.md", "r") as readme:
        DESCRIPTION = readme.read().decode("UTF-8")
else:
    with open("README.md", "r", encoding="UTF-8") as readme:
        DESCRIPTION = readme.read()


setup(
    name='beautysh',
    packages=['beautysh'],
    version=get_version(),
    description='A Bash beautifier for the masses.',
    long_description=DESCRIPTION,
    long_description_content_type="text/markdown",
    license='MIT',
    author='Bernardo Meurer',
    author_email='meurerbernardo@gmail.com',
    url='https://github.com/bemeurer/beautysh',
    download_url='https://github.com/bemeurer/beautysh/tarball/'+get_version(),
    keywords=['beautify', 'bash', 'shell', 'beautifier', 'script', 'auto'],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Filters",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Utilities"
    ],
    entry_points={'console_scripts': ['beautysh = beautysh.beautysh:main']},
    py_modules=['beautysh'],
    test_suite='nose.collector',
    tests_require=['nose']
)
