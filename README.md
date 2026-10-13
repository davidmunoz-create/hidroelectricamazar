# Hidrología CELEC Sur

Visualizador de caudales y cotas de los embalses de CELEC Sur (Mazar, Amaluza/Molino, Sopladora, Minas San Francisco y la cuenca del Paute), en vista diaria (por hora) y mensual (por día).

Fuente: https://generacioncsr.celec.gob.ec/graficasproduccion/index.html

## Archivos

- `index.html`: el visualizador.
- `data/diario.csv` y `data/mensual.csv`: los datos, con el mismo formato del botón "Descargar CSV" de CELEC.
- `scripts/actualizar.py`: descarga los datos del servicio de CELEC y reescribe los dos CSV.
- `.github/workflows/actualizar.yml`: ejecuta el script cada hora en GitHub y guarda los cambios.

## Publicar

1. Crear un repositorio público y subir todo el contenido de esta carpeta (incluida la carpeta oculta `.github`).
2. Settings → Pages → Source: "Deploy from a branch", rama `main`, carpeta `/ (root)`.
3. El visualizador queda en `https://USUARIO.github.io/REPOSITORIO/`.

## Insertar en la nota

```html
<iframe src="https://USUARIO.github.io/REPOSITORIO/" title="Caudales y niveles de los embalses de CELEC Sur" width="100%" height="900" style="border:0;" loading="lazy"></iframe>
```

Opciones en la dirección:

- `?embalse=mazar` (también `paute`, `amaluza`, `sopladora`, `msf`): embalse que aparece primero.
- `?periodo=mensual`: abre en la vista mensual.
- Se combinan así: `?periodo=mensual&embalse=amaluza`.

## Actualización

**Automática.** El flujo de GitHub Actions corre cada hora. Se revisa en la pestaña Actions; ahí también está el botón "Run workflow" para correrlo a mano. En Settings → Actions → General → Workflow permissions debe estar marcado "Read and write permissions".

**Manual.** En la página de CELEC, elegir Tipo "Hidrología", Periodo diario o mensual, pulsar "Descargar CSV" y subir el archivo a la carpeta `data/` con el nombre `diario.csv` o `mensual.csv` (Add file → Upload files, reemplazando el anterior).

**Desde una computadora.** Con Python instalado: `python scripts/actualizar.py` y luego subir los CSV. Se puede indicar una fecha: `python scripts/actualizar.py 2026-10-13`.

## Notas sobre los datos

- CELEC registra 0 cuando no hay dato; el visualizador los muestra como "sin dato".
- En el mensual, el caudal es el promedio del día y la cota es el valor al cierre del día (hora 24).
- Los rangos de operación (mínimo y máximo de cota) son los que publica la página de CELEC.
