import importlib
import logging
import pkgutil
import click
from pysim.sim import simulator
from pysim.sim.logger import ModelLoggerConfig


models_list = []  # Заполняется в коде инициализации, в конце файла


########################################
# CLI
########################################

# Корневая группа
@click.group
def cli():
    pass


# Вывести список моделей
@cli.command("list")
def list_models():
    for model_name in models_list:
        print(f"* {model_name}")


# Запустить модель. Команды в группу добавляются в коде инициализации ниже.
@cli.group("run")
def run():
    pass


@cli.command("sim")
def run_simulate():
    def initialize(sim: simulator.Simulator):
        sim.logger.info("запускаем инициализацию")

    logging.warning("calling simulate()")    
    simulator.simulate(
        model_name="dummy", 
        init=initialize, 
        max_num_events=1,
        logger_config=ModelLoggerConfig(
            file_name="model.log",
            file_level=logging.WARNING,
            file_name_no_run_id=True
        )
    )
    print("Just another line at the end (EOS)")



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
            module = importlib.import_module(".cli", f'pysim.models.{name}')            
            try:
                cmd : click.Command = getattr(module, "cli_run")
            except AttributeError:
                print(f"WARNING: no function 'cli_run(...)' found in {name}")
                continue
            if isinstance(cmd, click.Command):
                run.add_command(cmd, name)
                models_list.append(name)
            else:
                print("WARNING: cli_run() must be a Click command or group")
        except ModuleNotFoundError:
            pass

__initialize__()


if __name__ == '__main__':
    cli()
