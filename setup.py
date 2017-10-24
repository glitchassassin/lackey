""" Setup script for Lackey

"""
import re
import platform
from setuptools import setup, find_packages
from setuptools.dist import Distribution

with open('lackey/_version.py', 'r') as fd:
    __version__ = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                            fd.read(), re.MULTILINE).group(1)

class BinaryDistribution(Distribution):
    """ Custom class for platform-specific modules

    """
    def is_pure(self):
        return False

install_requires = ['requests', 'pillow', 'numpy', 'opencv-python', 'keyboard', 'pyperclip']
if platform.system() == "Darwin":
    install_requires += ['pyobjc']

setup(
    name="Lackey",
    description="A Sikuli script implementation in Python",
    long_description="""Lackey is an implementation of Sikuli script, using image recognition
    to control complex and non-OS-standard business applications. Potential applications include 
    automating tedious workflows, routine user interface testing, etc.""",
    url="https://github.com/glitchassassin/lackey",
    author="Jon Winsley",
    author_email="jon.winsley@gmail.com",
    license="MIT",
    version=__version__,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Software Development :: Testing",
        "Topic :: Utilities",
        "Topic :: Desktop Environment"
    ],
    keywords="automation testing sikuli",
    packages=find_packages(exclude=['docs', 'tests']),
    install_requires=install_requires,
    include_package_data=True,
    distclass=BinaryDistribution
)
