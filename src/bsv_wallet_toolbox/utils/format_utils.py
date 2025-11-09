"""Formatting utilities for BSV Wallet Toolbox.

Text alignment and display formatting utilities for logs and user output.

Reference: toolbox/ts-wallet-toolbox/src/utility/Format.ts
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bsv.beef import Beef
    from bsv.transaction import Transaction


class Format:
    """Static utility class for text and value formatting."""

    @staticmethod
    def align_left(value: str | int | float, fixed_width: int) -> str:
        """Align text to the left within fixed width, truncate if longer.

        Args:
            value: Value to align (converted to string)
            fixed_width: Target width in characters

        Returns:
            Left-aligned string padded to fixed_width, or truncated with '…' if too long

        Reference: toolbox/ts-wallet-toolbox/src/utility/Format.ts:7-13
        """
        value_str = str(value)
        if len(value_str) > fixed_width:
            return value_str[: fixed_width - 1] + "…"
        return value_str.ljust(fixed_width)

    @staticmethod
    def align_right(value: str | int | float, fixed_width: int) -> str:
        """Align text to the right within fixed width, truncate if longer.

        Args:
            value: Value to align (converted to string)
            fixed_width: Target width in characters

        Returns:
            Right-aligned string padded to fixed_width, or truncated with '…' if too long

        Reference: toolbox/ts-wallet-toolbox/src/utility/Format.ts:15-21
        """
        value_str = str(value)
        if len(value_str) > fixed_width:
            return "…" + value_str[-(fixed_width - 1) :]
        return value_str.rjust(fixed_width)

    @staticmethod
    def align_middle(value: str | int | float, fixed_width: int) -> str:
        """Align text to the middle within fixed width, truncate if longer.

        Args:
            value: Value to align (converted to string)
            fixed_width: Target width in characters

        Returns:
            Middle-aligned string, or truncated from ends if too long

        Reference: toolbox/ts-wallet-toolbox/src/utility/Format.ts:23-34
        """
        value_str = str(value)
        if len(value_str) == fixed_width:
            return value_str

        left_half = (fixed_width + 1) // 2  # Math.ceil(fixed_width / 2)
        right_half = fixed_width // 2  # Math.floor(fixed_width / 2)

        if len(value_str) > fixed_width:
            # Truncate from both ends
            left_part = value_str[:left_half]
            right_part = value_str[-(right_half):]
            return Format.align_left(left_part, left_half) + Format.align_right(right_part, right_half)

        # Pad on both sides
        left_pad_count = (len(value_str) + 1) // 2
        right_pad_count = len(value_str) // 2
        left_part = value_str[:left_pad_count]
        right_part = value_str[-right_pad_count:] if right_pad_count > 0 else ""

        return Format.align_right(left_part, left_half) + Format.align_left(right_part, right_half)

    @staticmethod
    def satoshis(satoshis: int) -> str:
        """Format satoshi amount with thousand separators and delimiters.

        Adds separators: underscores after every 2,6,10,14,18 positions
        (from right), period added at position 10.

        Args:
            satoshis: Amount in satoshis (can be negative)

        Returns:
            Formatted string with separators

        Reference: toolbox/ts-wallet-toolbox/src/utility/Format.ts:36-47
        """
        minus = "-" if satoshis < 0 else ""
        sat_abs = abs(satoshis)

        # Convert to list of digits
        digits = list(str(sat_abs))

        # Insert separators from the right
        # Positions (from right): 2, 6, 10, 14, 18
        insert_positions = [
            (len(digits) - 2, "_"),
            (len(digits) - 6, "_"),
            (len(digits) - 10, "."),
            (len(digits) - 14, "_"),
            (len(digits) - 18, "_"),
        ]

        # Sort by position descending to avoid index shifting
        for pos, sep in sorted(insert_positions, key=lambda x: -x[0]):
            if pos > 0:
                digits.insert(pos, sep)

        return minus + "".join(digits)

    @staticmethod
    def to_log_string_transaction(tx: Transaction) -> str:
        """Format Transaction as readable log string with inputs/outputs.

        Args:
            tx: Transaction object from bsv-sdk

        Returns:
            Formatted multi-line log string

        Reference: toolbox/ts-wallet-toolbox/src/utility/Format.ts:49-81
        """
        try:
            txid = tx.id("hex")
        except Exception as e:
            return f"Cannot get txid: {e!s}"

        try:
            log = ""
            total_in = 0
            total_out = 0

            max_io = max(len(tx.inputs), len(tx.outputs))

            for i in range(max_io):
                ilog = ""
                olog = ""

                if i < len(tx.inputs):
                    input_obj = tx.inputs[i]
                    satoshis = 0
                    if (
                        hasattr(input_obj, "source_transaction")
                        and input_obj.source_transaction
                        and hasattr(input_obj, "source_output_index")
                    ):
                        source_out = input_obj.source_transaction.outputs[input_obj.source_output_index]
                        satoshis = source_out.satoshis or 0
                    total_in += satoshis

                    source_txid = (input_obj.source_txid if hasattr(input_obj, "source_txid") else "") or ""
                    source_out_idx = input_obj.source_output_index if hasattr(input_obj, "source_output_index") else 0

                    ilog = (
                        f"{Format.align_left(Format.align_middle(source_txid, 12) + f'.{source_out_idx}', 17)} "
                        f"{Format.align_right(Format.satoshis(satoshis), 12)}"
                    )

                if i < len(tx.outputs):
                    output = tx.outputs[i]
                    satoshis = output.satoshis or 0
                    total_out += satoshis

                    script_hex = output.locking_script.to_hex()
                    script_len = len(script_hex)

                    olog = (
                        f"{Format.align_right(Format.satoshis(satoshis), 12)} "
                        f"({script_len})"
                        f"{Format.align_middle(script_hex, 13)}"
                    )

                log += f"{Format.align_left(ilog, 30)} " f"{Format.align_right(str(i), 5)} " f"{olog}\n"

            # Build header
            header = f"txid {txid}\n"
            header += (
                f"total in:{Format.satoshis(total_in)} "
                f"out:{Format.satoshis(total_out)} "
                f"fee:{Format.satoshis(total_in - total_out)}\n"
            )
            header += f"{Format.align_left('Inputs', 30)} " f"{Format.align_right('Vin/', 5)} " f"Outputs\n"
            header += (
                f"{Format.align_left('Outpoint', 17)} "
                f"{Format.align_right('Satoshis', 12)} "
                f"{Format.align_right('Vout', 5)} "
                f"{Format.align_right('Satoshis', 12)} "
                f"{Format.align_left('Lock Script', 23)}\n"
            )

            return header + log

        except Exception as _eu:
            return f"Transaction with txid {txid} is invalid"

    @staticmethod
    def to_log_string_beef_txid(beef: Beef, txid: str) -> str:
        """Format BEEF transaction as readable log string.

        Args:
            beef: Beef object from bsv-sdk
            txid: Transaction ID to find within beef

        Returns:
            Formatted log string, or error message if not found

        Reference: toolbox/ts-wallet-toolbox/src/utility/Format.ts:83-87
        """
        try:
            tx = beef.find_atomic_transaction(txid)
            if not tx:
                return f"Transaction {txid} not found in beef"
            return Format.to_log_string_transaction(tx)
        except Exception as e:
            return f"Cannot find transaction {txid} in beef: {e!s}"
