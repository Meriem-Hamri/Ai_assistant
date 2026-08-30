MIN_CHUNK_SIZE = 200
MAX_CHUNK_SIZE = 800


def is_too_small(
    text: str,
    min_length: int,
) -> bool:
    return len(text) < min_length


def is_too_large(
    text: str,
    max_length: int,
) -> bool:
    return len(text) > max_length


def is_valid_size(
    text: str,
    min_length: int,
    max_length: int,
) -> bool:
    return min_length <= len(text) <= max_length