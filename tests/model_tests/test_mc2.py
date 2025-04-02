from click.testing import CliRunner

from pysim.models.mc2.cli import cli_run


def test_calculate_correct_time():
    runner = CliRunner()
    time = 1
    time_delta = time * 0.1
    result = runner.invoke(
        cli_run,
        [
            '--probability', 1, 1, 1, 1, '--processing_time',
            time, time, time, time, '--max_transmisions', 100000
        ]
        )
    # Извлекаем время из вывода программы
    average_time = float((result.output.split('\n')[4]).split()[4])
    assert 4*time - time_delta <= average_time <= 4*time + time_delta
