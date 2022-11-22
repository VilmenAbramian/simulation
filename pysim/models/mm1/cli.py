import click

@click.group()
def cli_run():
    print("Running M/M/1 model")

@cli_run.command("a")
def run_1():
    print("AAAAA")


@cli_run.command("b")
def run_2():
    print("BBBBB")
    