"""Transaction size utilities (GO port)."""

from __future__ import annotations

from bsv_wallet_toolbox.errors import TransactionSizeError


def _varint_len(n: int) -> int:
    if n < 0:
        raise TransactionSizeError("negative size")
    if n <= 252:
        return 1
    if n <= 0xFFFF:
        return 3
    if n <= 0xFFFFFFFF:
        return 5
    return 9


def transaction_input_size(unlocking_script_size: int) -> int:
    return 40 + int(unlocking_script_size) + _varint_len(int(unlocking_script_size))


def transaction_output_size(locking_script_size: int) -> int:
    return 8 + int(locking_script_size) + _varint_len(int(locking_script_size))


def transaction_size(input_sizes: list[int], output_sizes: list[int]) -> int:
    size = 8  # tx envelope (version + locktime)
    try:
        size += _varint_len(len(input_sizes))
    except Exception as e:
        raise TransactionSizeError(str(e)) from e
    for s in input_sizes:
        try:
            size += transaction_input_size(int(s))
        except Exception as e:
            raise TransactionSizeError(str(e)) from e
    try:
        size += _varint_len(len(output_sizes))
    except Exception as e:
        raise TransactionSizeError(str(e)) from e
    for s in output_sizes:
        try:
            size += transaction_output_size(int(s))
        except Exception as e:
            raise TransactionSizeError(str(e)) from e
    return size


def inputs_outputs_sizes(
    unlocking_script_sizes: list[int], locking_script_sizes: list[int]
) -> tuple[list[int], list[int]]:
    """Return per-input and per-output sizes given script sizes.

    The input size is 40 + unlocking_size + varint_len(unlocking_size).
    The output size is 8 + locking_size + varint_len(locking_size).
    """
    inputs = [transaction_input_size(int(s)) for s in unlocking_script_sizes]
    outputs = [transaction_output_size(int(s)) for s in locking_script_sizes]
    return inputs, outputs
