from setuptools import setup, find_packages

setup(
    name="jocky-polymorphic-engine",
    version="1.0.0",
    description="JOCKY Polymorphic Engine - Makes every deployment unique",
    author="Member C",
    packages=find_packages(),
    install_requires=[
        'pefile>=2023.2.7',
        'cryptography>=41.0.7',
        'pycryptodome>=3.19.0',
        'capstone>=5.0.1',
        'lief>=0.13.2',
        'colorama>=0.4.6',
        'tqdm>=4.66.1',
        'pyelftools>=0.30',
        'macholib>=1.16.3',
        'astor>=0.8.1',
    ],
    python_requires='>=3.8',
)