import hashlib
import os
from dataclasses import dataclass


HASH_CHUNK_SIZE = 8192
OVERWRITE_CHUNK_SIZE = 1024 * 1024
VALID_KEEP_STRATEGIES = {"oldest", "newest", "path", "first"}


@dataclass
class DuplicateGroup:
    file_hash: str
    size_bytes: int
    keep: str
    delete: list[str]


@dataclass
class ScanResult:
    groups: list[DuplicateGroup]
    unreadable_files: list[str]
    target_directory: str | None = None


@dataclass
class DeleteFailure:
    path: str
    error: str


@dataclass
class DeleteResult:
    deleted_count: int
    failures: list[DeleteFailure]


def get_file_hash(filepath: str, chunk_size: int = HASH_CHUNK_SIZE) -> str | None:
    hasher = hashlib.sha256()
    try:
        with open(filepath, "rb") as handle:
            while True:
                chunk = handle.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except OSError:
        return None


def secure_delete(filepath: str, passes: int = 3) -> tuple[bool, str | None]:
    if passes < 1:
        raise ValueError("'passes' debe ser >= 1")

    try:
        file_size = os.path.getsize(filepath)
        with open(filepath, "r+b", buffering=0) as handle:
            for _ in range(passes):
                handle.seek(0)
                remaining = file_size
                while remaining > 0:
                    chunk_len = min(OVERWRITE_CHUNK_SIZE, remaining)
                    handle.write(os.urandom(chunk_len))
                    remaining -= chunk_len
                handle.flush()
                os.fsync(handle.fileno())

            handle.seek(0)
            handle.truncate(0)
            handle.flush()
            os.fsync(handle.fileno())

        os.remove(filepath)
        return True, None
    except OSError as exc:
        return False, str(exc)


def _safe_creation_time_ns(path: str) -> int:
    try:
        return os.stat(path).st_ctime_ns
    except OSError:
        return 2**63 - 1


def _keep_key(path: str, keep_strategy: str) -> tuple:
    created_ns = _safe_creation_time_ns(path)
    if keep_strategy == "oldest":
        return (created_ns, path)
    if keep_strategy == "newest":
        return (-created_ns, path)
    if keep_strategy == "path":
        return (path,)
    if keep_strategy == "first":
        return (0,)
    raise ValueError(f"Estrategia no soportada: {keep_strategy}")


def count_duplicate_files(scan_result: ScanResult) -> int:
    return sum(len(group.delete) for group in scan_result.groups)


def count_reclaimable_bytes(scan_result: ScanResult) -> int:
    return sum(len(group.delete) * group.size_bytes for group in scan_result.groups)


def _collect_size_to_files(directory: str, unreadable_files: list[str]) -> dict[int, list[str]]:
    size_to_files: dict[int, list[str]] = {}
    root = os.path.abspath(directory)

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            dirname
            for dirname in dirnames
            if not os.path.islink(os.path.join(dirpath, dirname))
        )
        filenames.sort()
        for filename in filenames:
            filepath = os.path.abspath(os.path.join(dirpath, filename))
            if os.path.islink(filepath):
                continue

            try:
                file_size = os.path.getsize(filepath)
            except OSError:
                unreadable_files.append(filepath)
                continue

            size_to_files.setdefault(file_size, []).append(filepath)

    return size_to_files


def _build_hash_map(
    size_to_files: dict[int, list[str]],
    unreadable_files: list[str],
    min_bucket_size: int = 1,
) -> dict[tuple[int, str], list[str]]:
    hash_to_files: dict[tuple[int, str], list[str]] = {}

    for file_size in sorted(size_to_files):
        candidate_paths = size_to_files[file_size]
        if len(candidate_paths) < min_bucket_size:
            continue

        for filepath in candidate_paths:
            file_hash = get_file_hash(filepath)
            if file_hash is None:
                unreadable_files.append(filepath)
                continue
            hash_to_files.setdefault((file_size, file_hash), []).append(filepath)

    return hash_to_files


def _validate_directory(path: str) -> str:
    absolute = os.path.abspath(path)
    if not os.path.isdir(absolute):
        raise NotADirectoryError(f"Directorio no valido: {path}")
    return absolute


def build_duplicate_plan(directory: str, keep_strategy: str = "oldest") -> ScanResult:
    absolute_directory = _validate_directory(directory)
    if keep_strategy not in VALID_KEEP_STRATEGIES:
        raise ValueError(f"Estrategia no soportada: {keep_strategy}")

    unreadable_files: list[str] = []
    size_to_files = _collect_size_to_files(absolute_directory, unreadable_files)
    hash_to_files = _build_hash_map(
        size_to_files=size_to_files,
        unreadable_files=unreadable_files,
        min_bucket_size=2,
    )

    groups: list[DuplicateGroup] = []
    for file_size, file_hash in sorted(hash_to_files):
        paths = hash_to_files[(file_size, file_hash)]
        if len(paths) < 2:
            continue
        ordered_paths = sorted(paths, key=lambda path: _keep_key(path, keep_strategy))
        groups.append(
            DuplicateGroup(
                file_hash=file_hash,
                size_bytes=file_size,
                keep=ordered_paths[0],
                delete=ordered_paths[1:],
            )
        )

    return ScanResult(
        groups=groups,
        unreadable_files=unreadable_files,
        target_directory=absolute_directory,
    )


def delete_duplicate_files(
    groups: list[DuplicateGroup],
    passes: int = 3,
) -> DeleteResult:
    deleted_count = 0
    failures: list[DeleteFailure] = []

    for group in groups:
        for target in group.delete:
            success, error = secure_delete(target, passes=passes)
            if success:
                deleted_count += 1
            else:
                failures.append(DeleteFailure(path=target, error=error or "Error desconocido"))

    return DeleteResult(
        deleted_count=deleted_count,
        failures=failures,
    )
