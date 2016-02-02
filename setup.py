"""Setup for beautysh - A bash beautifier for the masses."""
from setuptools import setup

setup(
    name='beautysh',
    packages=['beautysh'],
    version='1.0',
    description='A beautifier for Bash shell scripts written in Python.',
    license='GPL',
    author='Bernardo Meurer',
    author_email='meurerbernardo@gmail.com',
    url='https://github.com/bemeurer/beautysh',
    download_url='https://github.com/bemeurer/beautysh/tarball/1.0',
    keywords=['beautify', 'bash', 'shell', 'beautifier', 'script', 'auto'],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Filters",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Utilities"
        ],
    entry_points={'console_scripts': ['beautysh = beautysh.__main__:main']}
)
