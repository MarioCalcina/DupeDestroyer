import argparse

from dupe_core import build_duplicate_plan
from dupe_core import count_duplicate_files
from dupe_core import count_reclaimable_bytes
from dupe_core import delete_duplicate_files


def _format_bytes(total_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(total_bytes)
    unit_index = 0
    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1
    return f"{value:.2f} {units[unit_index]}"


def _print_plan(dry_run: bool, duplicates_count: int, reclaimable_bytes: int, scan_result) -> None:
    if not scan_result.groups:
        print("[i] No se encontraron duplicados.")
    else:
        print(f"[i] Grupos duplicados: {len(scan_result.groups)}")
        print(f"[i] Archivos a eliminar: {duplicates_count}")
        print(f"[i] Espacio recuperable aprox: {_format_bytes(reclaimable_bytes)}")
        for index, group in enumerate(scan_result.groups, start=1):
            print(f"\nGrupo {index} (hash={group.file_hash[:12]}...)")
            print(f"  Tamano por archivo: {_format_bytes(group.size_bytes)}")
            print(f"  Conservar: {group.keep}")
            for path in group.delete:
                action = "[Simulacion] Eliminar" if dry_run else "Eliminar"
                print(f"  {action}: {path}")

    if scan_result.unreadable_files:
        print(f"\n[!] Archivos no procesados por error de lectura: {len(scan_result.unreadable_files)}")
        for path in scan_result.unreadable_files:
            print(f"  - {path}")

    if dry_run:
        print("\n*** MODO SIMULACION ACTIVO ***")
        print("No se elimino ningun archivo.")


def _confirm_real_delete(duplicates_count: int) -> bool:
    prompt = (
        "\nVas a eliminar "
        f"{duplicates_count} archivos duplicados con eliminacion segura.\n"
        "Escribe ELIMINAR para continuar: "
    )
    return input(prompt).strip() == "ELIMINAR"


def find_and_delete_duplicates(
    directory: str,
    dry_run: bool = True,
    passes: int = 3,
    keep_strategy: str = "oldest",
    assume_yes: bool = False,
) -> None:
    print(f"[i] Escaneando: {directory}")
    print(f"[i] Estrategia para conservar: {keep_strategy}")

    try:
        scan_result = build_duplicate_plan(directory, keep_strategy)
    except (NotADirectoryError, ValueError) as exc:
        print(f"[-] {exc}")
        return

    duplicates_count = count_duplicate_files(scan_result)
    reclaimable_bytes = count_reclaimable_bytes(scan_result)
    _print_plan(
        dry_run=dry_run,
        duplicates_count=duplicates_count,
        reclaimable_bytes=reclaimable_bytes,
        scan_result=scan_result,
    )
    if duplicates_count == 0 or dry_run:
        return

    if not assume_yes and not _confirm_real_delete(duplicates_count=duplicates_count):
        print("[i] Operacion cancelada por el usuario.")
        return

    delete_result = delete_duplicate_files(
        groups=scan_result.groups,
        passes=passes,
    )
    failed_count = len(delete_result.failures)
    print(f"\nResumen: eliminados={delete_result.deleted_count}, fallidos={failed_count}")

    if failed_count:
        print("\nDetalle de fallos:")
        for failure in delete_result.failures:
            print(f"  - {failure.path}: {failure.error}")


def _run_gui() -> int:
    from gui import main as gui_main

    return gui_main()


def _should_open_gui(args: argparse.Namespace) -> bool:
    if args.cli:
        return False
    if args.gui:
        return True

    has_cli_intent = any(
        [
            args.directory != ".",
            args.apply,
            args.keep != "oldest",
            args.passes != 3,
            args.yes,
        ]
    )
    return not has_cli_intent


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detecta y elimina duplicados por contenido (CLI o GUI)."
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--gui",
        action="store_true",
        help="Abrir la interfaz grafica.",
    )
    mode_group.add_argument(
        "--cli",
        action="store_true",
        help="Forzar modo consola.",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directorio a escanear (por defecto: directorio actual).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Ejecuta eliminacion real. Sin este flag, solo simulacion.",
    )
    parser.add_argument(
        "--keep",
        choices=["oldest", "newest", "path", "first"],
        default="oldest",
        help="Regla para elegir la copia a conservar (oldest/newest usan fecha de creacion).",
    )
    parser.add_argument(
        "--passes",
        type=int,
        default=3,
        help="Numero de pasadas de sobrescritura al eliminar (default: 3).",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="No pedir confirmacion interactiva antes de eliminar.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    if _should_open_gui(args):
        raise SystemExit(_run_gui())

    find_and_delete_duplicates(
        directory=args.directory,
        dry_run=not args.apply,
        passes=args.passes,
        keep_strategy=args.keep,
        assume_yes=args.yes,
    )
