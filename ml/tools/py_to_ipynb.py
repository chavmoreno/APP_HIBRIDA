"""Convierte un script en formato "percent" (# %% / # %% [markdown]) a un notebook .ipynb.

Uso:
    python ml/tools/py_to_ipynb.py ml/stroke_prediction_colab.py ml/stroke_prediction_colab.ipynb

El .py es la fuente de verdad (fácil de revisar en diffs); el .ipynb se regenera con este script.
"""

import json
import re
import sys


def convertir(ruta_py: str, ruta_ipynb: str) -> None:
    """Lee el script, lo parte en celdas y escribe el notebook en formato nbformat 4."""
    with open(ruta_py, encoding="utf-8") as f:
        texto = f.read()

    # Cada celda empieza con una línea "# %%" (código) o "# %% [markdown]" (texto)
    bloques = re.split(r"^# %%(.*)$", texto, flags=re.MULTILINE)
    celdas = []
    # re.split devuelve [preambulo, cabecera1, cuerpo1, cabecera2, cuerpo2, ...]
    for cabecera, cuerpo in zip(bloques[1::2], bloques[2::2]):
        es_markdown = "[markdown]" in cabecera
        lineas = cuerpo.strip("\n").splitlines()
        if es_markdown:
            # Quita el prefijo "# " de cada línea de markdown
            lineas = [re.sub(r"^# ?", "", linea) for linea in lineas]
        fuente = [linea + "\n" for linea in lineas]
        if fuente:
            fuente[-1] = fuente[-1].rstrip("\n")  # La última línea no lleva salto
        celda = {"cell_type": "markdown" if es_markdown else "code", "metadata": {}, "source": fuente}
        if not es_markdown:
            celda.update({"execution_count": None, "outputs": []})
        celdas.append(celda)

    notebook = {
        "cells": celdas,
        "metadata": {
            "colab": {"provenance": []},
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 0,
    }
    with open(ruta_ipynb, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"{len(celdas)} celdas escritas en {ruta_ipynb}")


if __name__ == "__main__":
    convertir(sys.argv[1], sys.argv[2])
