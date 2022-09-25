from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read()
setup(
    name='procmux',
    version='1.0.0',
    author='Nick Pisani',
    author_email='napisani@yahoo.com',
    license='MIT',
    description='a TUI utility for running multiple commands in parallel in easily switchable terminals',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/napisani/procmux',
    py_modules=['procmux', 'app'],
    packages=find_packages(),
    install_requires=[requirements],
    python_requires='>=3.7',
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
    ],
    entry_points='''
        [console_scripts]
        procmux=procmux:start_cli
    '''
)
