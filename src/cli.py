# -*- coding: utf-8 -*-
import os

import click
import jinja2
import yaml
from dotenv import load_dotenv
import caseconverter


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


@cli.group()
def jinja():
    """"""


@jinja.command("make")
@click.option("-d", "--directory", default=".")
@click.option("--verbose", is_flag=True)
def jinja_make(verbose, directory):
    """"""
    root = directory
    load_dotenv(dotenv_path=f"{root}/.env")
    for directory_path, sub_directories_paths, files_names in os.walk(root):
        for file_name in files_names:
            file_path = f"{directory_path}/{file_name}"

            if not file_path.endswith(".jinja"):
                if verbose:
                    print(f"Skipping {file_path}")
                continue

            template_file_path = file_path

            if verbose:
                print(f"Processing {template_file_path}")

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
