# -*- coding: utf-8 -*-
import os
import re

import click
import jinja2
import yaml
from dotenv import load_dotenv
import caseconverter
from pprint import pprint

from src.packages.compose_file_names_validator import ComposeFileNamesValidator
from src.packages.compose_files_sorter import ComposeFilesSorter
import dotenv


@click.group()
@click.version_option()
def cli():
    """"""


@cli.group()
def docker():
    """"""


@cli.command()
def foo():
    """"""


@cli.command()
def bar():
    """"""


@docker.group("compose")
def docker_compose():
    """"""


@docker_compose.group("config")
def docker_compose_config():
    """"""


@docker_compose_config.command("find")
@click.option(
    "-d", "--directory",
    default=".", show_default=True,
)
@click.option(
    "--exclude",
    default=r"(\/vendor\/|\/node_modules\/)", show_default=True,
)
@click.option(
    "-e", "--environment",
    default="local", show_default=True,
    type=click.Choice(["local", "production", "development", "testing"]),
)
@click.option(
    "--raw",
    is_flag=True,
    default=False, show_default=True,
)
@click.option(
    "--overwrite-env-file",
    is_flag=True,
    default=False, show_default=True,
)
def docker_compose_config_find(directory, exclude, environment, raw, overwrite_env_file):
    """"""
    directory = os.path.abspath(directory)

    if not raw:
        print(f"Searching for docker-compose files in `{directory}` directory...")

    compose_files = []
    validator = ComposeFileNamesValidator(environment)

    for directory_path, sub_directories_paths, files_names in os.walk(directory):
        for file_name in files_names:
            file_path = f"{directory_path}/{file_name}"
            if validator.validate(file_name) and not re.search(exclude, file_path):
                compose_files.append(file_path.replace(directory + "/", ""))

    ComposeFilesSorter().sort(compose_files)

    compose_file_variable_value = ":".join(compose_files)

    if raw:
        print(compose_file_variable_value)
        exit(0)

    print("Collected compose files:")
    for compose_file in compose_files:
        print(f" - {compose_file}")

    if overwrite_env_file:
        env_file_path = f"{directory}/.env"
        print(f"Overwriting `{env_file_path}` file...")
        dotenv.set_key(env_file_path, "COMPOSE_FILE", compose_file_variable_value)


@cli.group()
def jinja():
    """"""


@jinja.command("make")
@click.option("-d", "--directory", default=".")
def jinja_make(directory):
    """"""
    root = directory
    load_dotenv(dotenv_path=f"{root}/.env")
    for directory_path, sub_directories_paths, files_names in os.walk(root):
        for file_name in files_names:
            file_path = f"{directory_path}/{file_name}"

            if not file_path.endswith(".jinja"):
                continue

            template_file_path = file_path

            result_file = template_file_path.replace(".jinja", "")

            jinja2_template_loader = jinja2.FileSystemLoader(searchpath='.')
            jinja2_env = jinja2.Environment(
                loader=jinja2_template_loader,
                autoescape=jinja2.select_autoescape()
            )
            jinja2_env.add_extension("jinja2.ext.loopcontrols")
            jinja2_env.globals["os"] = os
            jinja2_env.globals["root"] = root
            jinja2_env.globals["directory_path"] = directory_path
            jinja2_env.globals["directory_name"] = directory_path.split("/")[-1]
            jinja2_env.globals["file_path"] = file_path
            jinja2_env.globals["file_name"] = file_name
            jinja2_env.globals["yaml"] = yaml

            for case in ["camelcase", "kebabcase", "snakecase", "pascalcase", "flatcase", "cobolcase", "macrocase"]:
                jinja2_env.globals[case] = getattr(caseconverter, case)

            def include(file_name, globals=None):
                return jinja2_env.get_template(f"{directory_path}/{file_name}", globals=globals).render()

            jinja2_env.globals["include"] = include

            result = jinja2_env.get_template(template_file_path).render()
            open(result_file, "w").write(result)
