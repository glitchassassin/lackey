""" Setup script for Lackey

"""

from setuptools import setup, find_packages
from setuptools.dist import Distribution

class BinaryDistribution(Distribution):
    """ Custom class for platform-specific modules

    """
    def is_pure(self):
        return False

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
    install_requires=['requests', 'pillow', 'numpy', 'opencv-python'],
    include_package_data=True,
    distclass=BinaryDistribution
)
