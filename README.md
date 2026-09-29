# DupeDestroyer

Detecta archivos duplicados por contenido (hash SHA-256) y elimina duplicados de forma segura.

## Como funciona

- Escaneo recursivo de una carpeta.
- Filtro por tamano para acelerar busqueda.
- Verificacion final por hash para confirmar duplicados reales.
- Estrategia configurable para decidir cual archivo conservar:
  - `oldest` (primero creado)
  - `newest` (ultimo creado)
  - `path` (orden alfabetico de ruta)
  - `first` (primer archivo encontrado en el escaneo)
- Eliminacion segura irreversible por sobrescritura.

## Ejecucion principal (GUI)

```bash
uv run main.py
```

`main.py` abre la interfaz grafica por defecto.

## Modo consola (opcional)

Simulacion (no borra nada):

```bash
uv run main.py --cli "C:\\ruta\\a\\tu\\carpeta"
```

Eliminar duplicados de verdad:

```bash
uv run main.py --cli "C:\\ruta\\a\\tu\\carpeta" --apply --yes
```

Conservar el primer archivo encontrado:

```bash
uv run main.py --cli "C:\\ruta\\a\\tu\\carpeta" --keep first
```

Conservar el archivo que se creo primero:

```bash
uv run main.py --cli "C:\\ruta\\a\\tu\\carpeta" --keep oldest
```
