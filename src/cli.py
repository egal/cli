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
import inquirer
import semver


@click.group()
@click.version_option()
def cli():
    """"""


@cli.group("git")
def cli_git():
    """"""


@cli_git.group("version")
def cli_git_version():
    """"""


@cli_git_version.command("bump")
def cli_git_version_bump():
    """Bump version"""
    click.secho("Bumping version...", fg="green")

    last_tag = subprocess.run(["git", "describe", "--tags", "--abbrev=0", "--match", "v*.*.*"],
                              stdout=subprocess.PIPE).stdout.decode("utf-8")
    click.secho(f"Found latest version: {last_tag}", fg="yellow")

    version = semver.Version.parse(last_tag.removeprefix("v"))

    new_version_choose = inquirer.list_input(
        "Select version to bump",
        choices=[
            f"Alpha: v{version.bump_prerelease('alpha')}",
            f"Beta: v{version.bump_prerelease('beta')}",
            f"RC: v{version.bump_prerelease('rc')}",
            f"Patch: v{version.bump_patch()}",
            f"Minor: v{version.bump_minor()}",
            f"Major: v{version.bump_major()}",
        ],
    )
    new_tag = new_version_choose.split(": ")[1]

    click.secho(f"New version: {new_tag}, creating tag...", fg="yellow")
    subprocess.run(["git", "tag", new_tag])
    click.secho("Tag created", fg="green")


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
    "-o", "--output",
)
@click.option(
    "-m", "--mode",
    default="compose", show_default=True,
    type=click.Choice(["compose", "stack"]),
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False, show_default=False,
)
def docker_compose_config_collect(directory, mode, verbose, output):
    """Collect Docker Compose files into one file"""
    print("Collecting compose files...")
    directory = os.path.abspath(directory)
    if output is None:
        output = f"{directory}/docker-{mode}.yml"
    else:
        output = os.path.abspath(output)

    verbose and print(f"Output: {output}")

    docker_compose_config_cmd = subprocess.run(["docker", "compose", "config"], stdout=subprocess.PIPE)

    verbose and print(f"Command: {docker_compose_config_cmd.args}")
    stdout = docker_compose_config_cmd.stdout.decode("utf-8")
    verbose and print(f"Stdout: {stdout}")

    def yaml_int_constructor(loader, node):
        value = loader.construct_scalar(node)
        return int(value) if not value.startswith("0x") else value

    # Ignore HexInt parsing in yaml.SafeLoader
    yaml.add_constructor('tag:yaml.org,2002:int', yaml_int_constructor, Loader=yaml.SafeLoader)

    config = yaml.safe_load(stdout)
    verbose and print(f"Config: {config}")

    if config is None:
        print("ERROR: Error while getting config from Docker Compose CLI!")
        exit(1)

    if mode == "stack":
        del config["name"]
        if "services" in config:
            for service_name, service in config["services"].items():
                if "depends_on" in service:
                    service["depends_on"] = list(service["depends_on"].keys())
                if "ports" in service:
                    for port in service["ports"]:
                        if "published" in port and isinstance(port["published"], str):
                            port["published"] = int(port["published"])

    print(f"Writing config to `{output}` file...")
    if os.path.exists(output):
        print(f"WARNING: `{output}` file already exists and will be overwritten!")
    content = yaml.safe_dump(config)
    verbose and print(f"Content: {content}")
    open(output, "w").write(content)


@cli.group("jinja")
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
