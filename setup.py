from setuptools import setup, find_packages
from os import path

ROOT_DIR = path.abspath(path.dirname(__file__))

with open(path.join(ROOT_DIR, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="fritzbox_utils",
    version="0.1alpha",
    description="handy fritzbox utils",
    long_description=long_description,
    # url='',
    keywords="utilities, python, science",
    # classifiers=[
    #     'License :: OSI Approved :: MIT License',
    #     'Programming Language :: Python :: 3 :: Only',
    #     'Development Status :: 4 - Beta'
    # ],
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "fb_check = fritzbox_utils:check_status",
            "fb_ipy = fritzbox_utils:get_fb_ipy",
        ]
    },
    install_requires=[
        "black",
        "pre-commit",
        "matplotlib",
        "numpy",
        "pandas",
        "tabulate",
        "keyring",
        "fritzconnection",
    ],
    author="Felix Jung",
    author_email="jung@posteo.de",
)
