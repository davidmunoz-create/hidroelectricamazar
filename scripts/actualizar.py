#!/usr/bin/env python3
"""
Descarga la hidrología de CELEC Sur y regenera data/diario.csv y data/mensual.csv
con el mismo formato del botón "Descargar CSV" de la página de CELEC.

Uso:
    python scripts/actualizar.py              # día y mes actuales
    python scripts/actualizar.py 2026-10-13   # un día concreto (y su mes)

Solo usa la biblioteca estándar de Python 3.8 o superior.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

BASE = "https://generacioncsr.celec.gob.ec:8443/ords/csr/sardomcsr/"
ECUADOR = timezone(timedelta(hours=-5))
CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

# Código de cada medición en el sistema de CELEC Sur (comprobado contra sus CSV).
# Para el mensual, los caudales son promedio del día y las cotas, el valor de la hora 24.
COLUMNAS = [
    ("CaudalCuencaPaute", 24812, "cuenca"),
    ("CaudalMol", 24811, "promedio"),
    ("CotaMol", 24019, "cierre"),
    ("CaudalMaz", 30538, "promedio"),
    ("CotaMaz", 30031, "cierre"),
    ("CaudalSop", 90537, "promedio"),
    ("CotaSop", 90919, "cierre"),
    ("CaudalMsf", 650538, "promedio"),
    ("CotaMsf", 650919, "cierre"),
]
SERVICIO_MENSUAL = {
    "promedio": "pointValuesMesAvg",
    "cierre": "pointValuesMesH24",
    "cuenca": "csrCaudCuenMesAvg",
}


def iso_utc(d):
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def consultar(servicio, inicio, fin, mrid=None, intentos=3):
    params = {
        "fechaInicio": iso_utc(inicio),
        "fechaFin": iso_utc(fin),
        "fecha": inicio.strftime("%d/%m/%Y %H:%M:%S"),
    }
    if mrid is not None:
        params["mrid"] = mrid
    url = BASE + servicio + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (visualizador hidrologia CELEC Sur)",
        "Accept": "application/json",
        "Origin": "https://generacioncsr.celec.gob.ec",
        "Referer": "https://generacioncsr.celec.gob.ec/graficasproduccion/index.html",
    })
    ultimo_error = None
    for i in range(intentos):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                items = json.loads(r.read().decode("utf-8")).get("items", [])
            salida = {}
            for it in items:
                t = datetime.strptime(it["loctimestamp"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                salida[t.astimezone(ECUADOR).replace(tzinfo=None)] = it.get("valueedit")
            return salida
        except Exception as e:  # noqa: BLE001
            ultimo_error = e
            time.sleep(5 * (i + 1))
    raise RuntimeError("No se pudo consultar %s (mrid %s): %s" % (servicio, mrid, ultimo_error))


def escribir(nombre, filas):
    """filas: lista de (fecha, {columna: valor}) ordenada de la más reciente a la más antigua."""
    ruta = os.path.join(CARPETA, nombre)
    lineas = ["Fecha," + ",".join(c for c, _, _ in COLUMNAS)]
    for fecha, valores in filas:
        celdas = []
        for col, _, _ in COLUMNAS:
            v = valores.get(col)
            celdas.append("" if v is None else repr(float(v)).rstrip("0").rstrip("."))
        lineas.append('"%s",%s' % (fecha.strftime("%d/%m/%Y %H:%M:%S"), ",".join(celdas)))
    contenido = "\n".join(lineas) + "\n"
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(contenido)
    return ruta


def tiene_datos(filas):
    return any(v is not None for _, valores in filas for v in valores.values())


def diario(dia):
    inicio = datetime(dia.year, dia.month, dia.day, 1, tzinfo=ECUADOR)
    fin = inicio + timedelta(days=1)
    horas = [(inicio + timedelta(hours=h)).replace(tzinfo=None) for h in range(24)]
    series = {col: consultar("pointValues", inicio, fin, mrid) for col, mrid, _ in COLUMNAS}
    filas = [(h, {col: series[col].get(h) for col, _, _ in COLUMNAS}) for h in horas]
    return list(reversed(filas))


def mensual(dia):
    inicio = datetime(dia.year, dia.month, 1, 1, tzinfo=ECUADOR)
    sig = datetime(dia.year + (dia.month == 12), dia.month % 12 + 1, 1, 1, tzinfo=ECUADOR)
    dias = []
    d = datetime(dia.year, dia.month, 1)
    while d.month == dia.month:
        dias.append(d)
        d += timedelta(days=1)
    series = {}
    for col, mrid, tipo in COLUMNAS:
        servicio = SERVICIO_MENSUAL[tipo]
        series[col] = consultar(servicio, inicio, sig, None if tipo == "cuenca" else mrid)
    filas = [(d, {col: series[col].get(d) for col, _, _ in COLUMNAS}) for d in dias]
    return list(reversed(filas))


def main():
    if len(sys.argv) > 1:
        dia = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
        forzado = True
    else:
        dia = datetime.now(ECUADOR).date()
        forzado = False

    filas_dia = diario(dia)
    # Entre la medianoche y la 01:00 todavía no hay registros del día: se muestra el anterior.
    if not tiene_datos(filas_dia) and not forzado:
        dia = dia - timedelta(days=1)
        filas_dia = diario(dia)
    if not tiene_datos(filas_dia):
        print("CELEC no devolvió datos para el %s; no se modifica nada." % dia)
        return 0

    print("Escrito", escribir("diario.csv", filas_dia))
    filas_mes = mensual(dia)
    if tiene_datos(filas_mes):
        print("Escrito", escribir("mensual.csv", filas_mes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
