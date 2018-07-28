import setuptools

setuptools.setup(
	name="Alien Shower",
	use_scm_version=True,
	description="A kind of round-based space invader tetris mix.",
	long_description="Just try it.",
	author="Kjili",
	author_email="Kjili@users.noreply.github.com",
	url="https://github.com/Kjili/AlienShower",
	py_modules=["alien_shower"],
	# requirements
	setup_requires=["setuptools_scm",],
	python_requires=">=3.6",
	# further description
	keywords="game",
	classifiers=[
		"Development Status :: 5 - Production/Stable",
		"Environment :: Console :: Curses",
		"Intended Audience :: End Users/Desktop",
		"License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
		"Natural Language :: English",
		"Operating System :: Unix",
		"Programming Language :: Python :: 3",
		"Programming Language :: Python :: 3.6",
		"Topic :: Games/Entertainment",
		"Topic :: Games/Entertainment :: Arcade",
		"Topic :: Games/Entertainment :: Puzzle Games"
	],
)
