# -*- coding: utf-8 -*-
import os
import subprocess
import click
import jinja2
import yaml
from dotenv import load_dotenv
import caseconverter
from src.packages.compose_files_finder import ComposeFilesFinder
import dotenv


@click.group()
@click.version_option()
def cli():
    """"""


@cli.command("list")
def cli_list():
    print("Available commands:")

    def command_tree(command, previous_command_prefix=None):
        if previous_command_prefix == "cli":
            previous_command_prefix = None

        if isinstance(command, click.core.Group):
            for sub_command in command.commands.values():
                command_tree(
                    sub_command,
                    f"{previous_command_prefix} {command.name}" if previous_command_prefix else command.name
                )
        else:
            output = " - "
            if previous_command_prefix:
                output += f"{previous_command_prefix} "
            output += command.name
            help = command.get_short_help_str()
            if help:
                output += " : " + help
            print(output)

    command_tree(cli)


@cli.group("docker")
def cli_docker():
    """"""


@cli_docker.group("compose")
def cli_docker_compose():
    """"""


@cli_docker_compose.group("config")
def cli_docker_compose_config():
    """"""


@cli_docker_compose_config.command("find")
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
def cli_docker_compose_config_find(directory, raw, overwrite_env_file, environment, exclude):
    """Find Docker Compose files"""
    directory = os.path.abspath(directory)

    if not raw:
        print(f"Searching for docker-compose files in `{directory}` directory...")

    finder = ComposeFilesFinder(directory, environment, exclude)

    if raw:
        print(finder.get_files_as_raw())
        exit(0)

    print("Collected compose files:")
    for compose_file in finder.files:
        print(f" - {compose_file}")

    if overwrite_env_file:
        env_file_path = f"{directory}/.env"
        print(f"Overwriting `{env_file_path}` file...")
        dotenv.set_key(env_file_path, "COMPOSE_FILE", finder.get_files_as_raw())


@cli_docker_compose_config.command("collect")
@click.option(
    "-d", "--directory",
    default=".", show_default=True,
)
@click.option(
    "-m", "--mode",
    default="compose", show_default=True,
    type=click.Choice(["compose", "stack"]),
)
def docker_compose_config_collect(directory, mode):
    """Collect Docker Compose files into one file"""
    print("Collecting compose files...")
    directory = os.path.abspath(directory)
    load_dotenv(dotenv_path=f"{directory}/.env")
    compose_files = os.getenv("COMPOSE_FILE")

    compose_options = []
    for file in compose_files.split(":"):
        compose_options.extend(["-f", file])

    docker_compose_config_cmd = subprocess.run([
        "docker", "compose",
        *compose_options,
        "config",
    ], stdout=subprocess.PIPE)

    config = yaml.safe_load(docker_compose_config_cmd.stdout.decode("utf-8"))

    if mode == "stack":
        del config["name"]
        for service_name, service in config["services"].items():
            if "depends_on" in service:
                service["depends_on"] = list(service["depends_on"].keys())
            if "ports" in service:
                for port in service["ports"]:
                    if "published" in port and isinstance(port["published"], str):
                        port["published"] = int(port["published"])

    output_file_path = f"{directory}/docker-{mode}.yml"
    print(f"Writing config to `{output_file_path}` file...")
    open(output_file_path, "w").write(yaml.safe_dump(config))


@cli.group()
def cli_jinja():
    """"""


@cli_jinja.command("make")
@click.option("-d", "--directory", default=".")
def cli_jinja_make(directory):
    """Find and make files from Jinja templates"""
    print("Making files from Jinja templates...")
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
