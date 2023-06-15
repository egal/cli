from setuptools import setup

requirements = []
for require in open("requirements.txt", "r").read().split("\n"):
    if require != "":
        requirements.append(require)

setup(
    name="egal-cli",
    packages=["src"],
    include_package_data=True,
    install_requires=requirements,
    entry_points="""
        [console_scripts]
        egal=src.cli:cli
    """,
    setuptools_git_versioning={
        "enabled": True,
    },
    setup_requires=["setuptools-git-versioning<2"],
)
