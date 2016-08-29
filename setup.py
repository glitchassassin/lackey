from setuptools import setup, find_packages
from setuptools.dist import Distribution

class BinaryDistribution(Distribution):
    def is_pure(self):
        return False

setup(
	name="Lackey",
	version="0.2.1a1",
	description="A graphical automation framework for Python",
	long_description="Lackey is a flexible automation framework using image recognition to reliably control complex and non-OS-standard business applications. Potential applications include automating tedious workflows, routine user interface testing, etc. Lackey can also run Sikuli scripts with the help of a shim.",
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
	install_requires=['pillow', 'numpy'],
	package_data={
		'': ['cv2.pyd']
	},
	include_package_data=True,
	distclass=BinaryDistribution
)