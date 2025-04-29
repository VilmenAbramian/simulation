import locale
import matplotlib
import matplotlib.pyplot as plt
import os
import platform
from typing import Sequence


class GraphConsts:
    """
    Класс для хранения констант оформления графиков.
    """
    CMAP_NAME = 'inferno'             # Цветовая схема для графиков
    IMAGE_BASE_DIR = 'result_images'         # Папка для сохранения изображений
    IMAGE_EXTENSIONS = ('pdf', 'png') # Расширения файлов для сохранения
    FONT_SIZE = 16
    FIGSIZE = (8, 5)
    LEGEND_FONTSIZE = 14 # Легенда чуть меньше
    LINEWIDTH = 2
    MARKERSIZE = 8
    MARKEVERY = 20



def setup_matplotlib() -> None:
    """
    Настроить параметры matplotlib и локали.
    """
    matplotlib.rcParams.update({
        'image.cmap': GraphConsts.CMAP_NAME,
        'axes.formatter.use_locale': True,
        'font.size': GraphConsts.FONT_SIZE,
        'font.family': 'sans-serif',
        'lines.linewidth': GraphConsts.LINEWIDTH,
        'lines.markersize': GraphConsts.MARKERSIZE,
        'legend.fontsize': GraphConsts.LEGEND_FONTSIZE,
        'figure.figsize': GraphConsts.FIGSIZE,

        # Шрифт PT Serif Caption можно установить с Google Fonts.
        # После установки шрифта нужно удалить кэш matplitlib,
        # на Ubuntu: ~/.cache/matplotlib
        'font.sans-serif': ['PT Serif Caption',],
    })
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')


def get_color(x: float):
    """
    Получить цвет из текущей карты.

    Args:
        x (float): число от 0 до 1

    Returns:
        color
    """
    return matplotlib.cm.get_cmap(GraphConsts.CMAP_NAME)(x)


def savefig(name: str, exts: Sequence[str] = GraphConsts.IMAGE_EXTENSIONS,
            directory: str = 'res_img') -> None:
    """
    Сохранить изображение в файлы с общим именем и разными расширениями.
    Изображения будут сохранены в папку GraphConsts.IMAGE_BASE_DIR/directory.

    Если name - пустая строка, ничего сохраняться не будет.

    Args:
        name (str): название файла без расширения
        exts (list of str): набор расширений, по-умолчанию png и pdf
        directory (str): подкаталог внутри IMAGE_BASE_DIR
    """
    if name is None:
        return
    name = name.strip()
    if name:
        save_dir = os.path.join(GraphConsts.IMAGE_BASE_DIR, directory)
        os.makedirs(save_dir, exist_ok=True)
        for ext in exts:
            file_path = os.path.join(save_dir, f"{name}.{ext}")
            plt.savefig(file_path, bbox_inches="tight")


def set_axes_formatter(
        *axes,
        use_x: bool = False,
        use_y: bool = False,
        platforms: Sequence[str] = ("Linux",)
) -> None:
    """
    У некоторых нормальных шрифтов нет глифов, которые нужны
    в русской локали. Поэтому стараемся избежать ситуации,
    когда эти глифы нужны.

    Сейчас обходим глиф-пробел 8239 в формате больших целых.

    Args:
        axes (list of Axes): графики, к которым применить
        use_x (bool): применять ли к OX (False)
        use_y (bool): применять ли к OY (False)
        platforms (list of str): на каких платформах надо применять ("Linux")
    """
    def fmt(value, tick_num):
        if isinstance(value, int):
            return f"{value:g}"
        elif isinstance(value, float):
            if int(value) == value:
                return f"{value:g}"
            else:
                return f"{value:n}"
        return str(value)

    if not platforms or platform.system() in platforms:
        for axes_ in axes:
            if not (isinstance(axes_, list) or isinstance(axes_, tuple)):
                axes_ = (axes_,)
            for ax in axes_:
                if use_y:
                    ax.yaxis.set_major_formatter(plt.FuncFormatter(fmt))
                if use_x:
                    ax.xaxis.set_major_formatter(plt.FuncFormatter(fmt))
