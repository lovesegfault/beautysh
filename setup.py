"""Setup for beautysh - A bash beautifier for the masses."""
from setuptools import setup


def get_version(file_name='beautysh/__init__.py'):
    """Get version info from __init__."""
    with open(file_name) as f:
        for line in f:
            if "__version__" in line:
                return eval(line.split('=')[-1])


setup(
    name='beautysh',
    packages=['beautysh'],
    version=get_version(),
    description='A Bash beautifier for the masses.',
    license='GPL',
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
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPL"
        "v3)",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Filters",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Utilities"
    ],
    entry_points={'console_scripts': ['beautysh = beautysh.beautysh:main']},
    py_modules=['beautysh']
)
