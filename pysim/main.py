import click
import importlib
import pkgutil


models_list = []  # Заполняется в коде инициализации, в конце файла


# Создаёт корневую команду sim, к которой можно добавлять подкоманды.
@click.group
def cli():
    pass


@cli.command('list')
def list_models():
    """Выводит список моделей."""
    for model_name in models_list:
        print(f"* {model_name}")


@cli.group('run')
def run():
    """Запустить модель."""
    pass


#############################################################################
# ИНИЦИАЛИЗАЦИЯ
#
# Просматриваем все подмодули в модуле models.
# Для каждого подмодуля, в котором есть файл cli.py, и в котором есть команда
# click `run()`, то есть функция вида добавляем в качестве подкоманды в группу
# `run`, в качестве имени используем название подмодуля.
#
# Имена таких подмодулей (моделей) сохраняем в массиве models, их можно
# вывести c помощью команды `sim list`.
#
# Например, если есть модуль `models.echo`, в нем есть `cli.py`,
# и в нем есть функция run():
#
# -----------------------------------------------------
# # File: models.echo.cli.py
#
# @click.command
# def run():
#     print("Hello, I am an echo protocol model")
# ----------------------------------------------------
#
# Тогда в CLI будет добавлена команда `sim run echo`:
#
# > sim run echo
# Hello, I am an echo protocol model
#
# > sim list
# * echo
#############################################################################
def __initialize__():
    from pysim import models  # type: ignore
    for submodule in pkgutil.iter_modules(models.__path__):
        name = submodule.name
        try:
            module = importlib.import_module('.cli', f'pysim.models.{name}')
            try:
                cmd: click.Command = getattr(module, "cli_run")
            except AttributeError:
                print(f"WARNING: no function 'cli_run(...)' found in {name}")
                continue
            if isinstance(cmd, click.Command):
                run.add_command(cmd, name)
                models_list.append(name)
            else:
                print("WARNING: cli_run() must be a Click command or group")
        except ModuleNotFoundError:
            print(f'В модуле {name} некорректное оформление!')


__initialize__()


if __name__ == '__main__':
    cli()
