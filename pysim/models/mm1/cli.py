import click

@click.group()
def run():
    print("Running M/M/1 model")

@run.command("a")
def run_1():
    print("AAAAA")


@run.command("b")
def run_2():
    print("BBBBB")
    