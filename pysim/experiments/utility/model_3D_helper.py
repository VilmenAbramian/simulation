import numpy as np
import plotly.graph_objects as go


def plot_vector(fig, start, end, color="red", name=None):
    """
    Построить вектор.

    Args:
        fig: объект plotly.graph_objects
        start (np.array(x,y,z)): координаты начала вектора
        end (np.array(x,y,z)): координаты конца вектора
        color (str): цвет линии вектора
        name (None|str): имя вектора для легенды

    """
    vector = np.array(end) - np.array(start)
    fig.add_trace(go.Scatter3d(
        x=[start[0], end[0]],
        y=[start[1], end[1]],
        z=[start[2], end[2]],
        mode="lines+markers",
        line=dict(color=color, width=5),
        marker=dict(size=4),
        name=name or f"Vector {vector}"
    ))


def plot_point(fig, point, color="blue", name=None):
    """
    Построить точку.

    Args:
        fig: объект plotly.graph_objects
        point (np.array(x,y,z)): координаты точки
        color (str): цвет точки
        name (None|str): имя точки для легенды

    """
    fig.add_trace(go.Scatter3d(
        x=[point[0]], y=[point[1]], z=[point[2]],
        mode="markers",
        marker=dict(size=6, color=color),
        name=name or f"Point {point}"
    ))


def plot_plane(fig, normal, point_on_plane, size=10, color="lightblue", opacity=0.5):
    """
    Построить плоскость.

    Args:
        fig: объект plotly.graph_objects
        normal (np.array(x,y,z)): координаты нормального к плоскости вектора
        point_on_plane (np.array(x,y,z)): точка на плоскости
        size (int): размеры плоскости (size x size)
        color (str): цвет плоскости
        opacity (float): прозрачность плоскости
    """
    normal = np.array(normal)
    point = np.array(point_on_plane)

    d = -np.dot(normal, point)

    # Определим, какую координату выразим
    a, b, c = normal
    grid_pts = np.linspace(-size, size, 10)

    if abs(c) > 1e-6:
        X, Y = np.meshgrid(grid_pts, grid_pts)
        Z = (-a * X - b * Y - d) / c
    elif abs(b) > 1e-6:
        X, Z = np.meshgrid(grid_pts, grid_pts)
        Y = (-a * X - c * Z - d) / b
    elif abs(a) > 1e-6:
        Y, Z = np.meshgrid(grid_pts, grid_pts)
        X = (-b * Y - c * Z - d) / a
    else:
        raise ValueError("Недопустимая нормаль: нормаль не должна быть нулевым вектором.")

    fig.add_trace(go.Surface(
        x=X, y=Y, z=Z,
        opacity=opacity,
        colorscale=[[0, color], [1, color]],
        showscale=False
    ))


def draw_axes(fig, length=10):
    """
    Построить оси OX, OY, OZ.

    Args:
        fig: объект plotly.graph_objects
        length (int): длина осей
    """
    fig.add_trace(go.Scatter3d(x=[-length, length], y=[0, 0], z=[0, 0], mode="lines", line=dict(width=8, color="black"),
                               name="OX"))
    fig.add_trace(go.Scatter3d(x=[0, 0], y=[-length, length], z=[0, 0], mode="lines", line=dict(width=8, color="black"),
                               name="OY"))
    fig.add_trace(go.Scatter3d(x=[0, 0], y=[0, 0], z=[-length, length], mode="lines", line=dict(width=8, color="black"),
                               name="OZ"))

    # Стрелки
    fig.add_trace(go.Cone(
        x=[length], y=[0], z=[0], u=[1], v=[0], w=[0], sizemode="absolute", sizeref=2, anchor="tail", showscale=False,
        colorscale=[[0, "black"], [1, "black"]]))
    fig.add_trace(go.Cone(
        x=[0], y=[length], z=[0], u=[0], v=[1], w=[0], sizemode="absolute", sizeref=2, anchor="tail", showscale=False,
        colorscale=[[0, "black"], [1, "black"]]))
    fig.add_trace(go.Cone(
        x=[0], y=[0], z=[length], u=[0], v=[0], w=[1], sizemode="absolute", sizeref=2, anchor="tail", showscale=False,
        colorscale=[[0, "black"], [1, "black"]]))

    # Подписи
    fig.add_trace(go.Scatter3d(x=[length + 1], y=[0], z=[0], mode="text", text=["X"], textposition="top right", name="",
                               showlegend=False))
    fig.add_trace(go.Scatter3d(x=[0], y=[length + 1], z=[0], mode="text", text=["Y"], textposition="top right", name="",
                               showlegend=False))
    fig.add_trace(go.Scatter3d(x=[0], y=[0], z=[length + 1], mode="text", text=["Z"], textposition="top right", name="",
                               showlegend=False))