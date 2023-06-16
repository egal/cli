from setuptools import setup

requirements = ["setuptools-git-versioning==1.13.3"]
for require in open("requirements.txt", "r").read().split("\n"):
    if require != "":
        requirements.append(require)

setup(
    name="egal-cli",
    packages=["src", "src.packages"],
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
