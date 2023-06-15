import os
from dotenv import load_dotenv

from setuptools import setup

requirements = []
for require in open("requirements.txt", "r").read().split("\n"):
    if require != "":
        requirements.append(require)

load_dotenv(dotenv_path=f"{os.getcwd()}/.env")

version = os.getenv("VERSION")
if version is None:
    raise Exception("VERSION is not set")

setup(
    name="egal-cli",
    version="1.0",
    packages=["src"],
    include_package_data=True,
    install_requires=requirements,
    entry_points="""
        [console_scripts]
        egal=src.cli:cli
    """,
)
