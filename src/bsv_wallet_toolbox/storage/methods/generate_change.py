from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Protocol

from bsv_wallet_toolbox.errors import InvalidParameterError, WalletError
from bsv_wallet_toolbox.utils.validation import validate_satoshis

# Constants
MAX_POSSIBLE_SATOSHIS = 2099999999999999


class InternalError(WalletError):
    """Internal logic error."""

    def __init__(self, message: str = "Internal error"):
        super().__init__(message)


class InsufficientFundsError(WalletError):
    """Insufficient funds for transaction."""

    def __init__(self, total_satoshis_needed: int, more_satoshis_needed: int):
        message = (
            f"Insufficient funds in the available inputs to cover the cost of the required outputs "
            f"and the transaction fee ({more_satoshis_needed} more satoshis are needed, "
            f"for a total of {total_satoshis_needed}), plus whatever would be required in order to "
            f"pay the fee to unlock and spend the outputs used to provide the additional satoshis."
        )
        super().__init__(message)
        self.required = total_satoshis_needed
        self.short = more_satoshis_needed


@dataclass
class GenerateChangeSdkInput:
    satoshis: int
    unlocking_script_length: int


@dataclass
class GenerateChangeSdkOutput:
    satoshis: int
    locking_script_length: int


@dataclass
class GenerateChangeSdkFundingInput:
    output_id: int
    satoshis: int


@dataclass
class GenerateChangeSdkChangeOutput:
    satoshis: int
    locking_script_length: int


@dataclass
class StorageFeeModel:
    model: str
    value: float


@dataclass
class GenerateChangeSdkParams:
    fixed_inputs: list[GenerateChangeSdkInput]
    fixed_outputs: list[GenerateChangeSdkOutput]
    fee_model: StorageFeeModel
    change_initial_satoshis: int
    change_first_satoshis: int
    change_locking_script_length: int
    change_unlocking_script_length: int
    target_net_count: int = 0
    random_vals: list[float] | None = None
    no_logging: bool = False
    log: str | None = None


@dataclass
class GenerateChangeSdkResult:
    allocated_funding_inputs: list[GenerateChangeSdkFundingInput]
    change_outputs: list[GenerateChangeSdkChangeOutput]
    size: int
    fee: int
    sats_per_kb: float
    max_possible_satoshis_adjustment: dict[str, int] | None = None


class AllocateFundingInputCallback(Protocol):
    def __call__(
        self, target_satoshis: int, exact_satoshis: int | None = None
    ) -> GenerateChangeSdkFundingInput | None: ...


class ReleaseFundingInputCallback(Protocol):
    def __call__(self, output_id: int) -> None: ...


def validate_generate_change_sdk_params(params: GenerateChangeSdkParams) -> dict[str, Any]:
    if not isinstance(params.fixed_inputs, list):
        raise InvalidParameterError("fixedInputs", "an array of objects")

    r: dict[str, Any] = {}

    for i, x in enumerate(params.fixed_inputs):
        validate_satoshis(x.satoshis, f"fixedInputs[{i}].satoshis")
        if not isinstance(x.unlocking_script_length, int) or x.unlocking_script_length < 0:
            raise InvalidParameterError(f"fixedInputs[{i}].unlockingScriptLength", "integer >= 0")

    if not isinstance(params.fixed_outputs, list):
        raise InvalidParameterError("fixedOutputs", "an array of objects")

    for i, x in enumerate(params.fixed_outputs):
        validate_satoshis(x.satoshis, f"fixedOutputs[{i}].satoshis")
        if not isinstance(x.locking_script_length, int) or x.locking_script_length < 0:
            raise InvalidParameterError(f"fixedOutputs[{i}].lockingScriptLength", "integer >= 0")
        if x.satoshis == MAX_POSSIBLE_SATOSHIS:
            if "has_max_possible_output" in r:
                raise InvalidParameterError(
                    f"fixedOutputs[{i}].satoshis",
                    "valid satoshis amount. Only one 'maxPossibleSatoshis' output allowed.",
                )
            r["hasMaxPossibleOutput"] = i

    if params.fee_model.model != "sat/kb":
        raise InvalidParameterError("feeModel.model", "'sat/kb'")

    validate_satoshis(params.change_first_satoshis, "changeFirstSatoshis")
    validate_satoshis(params.change_initial_satoshis, "changeInitialSatoshis")

    if not isinstance(params.change_locking_script_length, int):
        raise InvalidParameterError("changeLockingScriptLength", "integer")
    if not isinstance(params.change_unlocking_script_length, int):
        raise InvalidParameterError("changeUnlockingScriptLength", "integer")

    return r


def transaction_size(input_script_lengths: list[int], output_script_lengths: list[int]) -> int:
    def varint_len(n: int) -> int:
        if n < 0xFD:
            return 1
        if n <= 0xFFFF:
            return 3
        if n <= 0xFFFFFFFF:
            return 5
        return 9

    size = 4 + 4 + varint_len(len(input_script_lengths)) + varint_len(len(output_script_lengths))

    for length in input_script_lengths:
        size += 36 + varint_len(length) + length + 4

    for length in output_script_lengths:
        size += 8 + varint_len(length) + length

    return size


def generate_change_sdk(
    params: GenerateChangeSdkParams,
    allocate_funding_input: AllocateFundingInputCallback,
    release_funding_input: ReleaseFundingInputCallback,
) -> GenerateChangeSdkResult:
    """
    Simplified port of generateChangeSdk from TypeScript.
    """
    r = GenerateChangeSdkResult(allocated_funding_inputs=[], change_outputs=[], size=0, fee=0, sats_per_kb=0)

    try:
        vgcpr = validate_generate_change_sdk_params(params)
        sats_per_kb = params.fee_model.value or 0

        random_vals = list(params.random_vals or [])
        random_vals_used: list[float] = []

        def next_random_val() -> float:
            if not random_vals:
                val = random.random()
            else:
                val = random_vals.pop(0)
                random_vals.append(
                    val
                )  # cycle if depleted? or just pop? TS code: shift() || 0 and push(val). So it cycles.
            random_vals_used.append(val)
            return val

        def rand(min_val: int, max_val: int) -> int:
            if max_val < min_val:
                raise InvalidParameterError("max", f"less than min ({min_val}). max is ({max_val})")
            return math.floor(next_random_val() * (max_val - min_val + 1) + min_val)

        fixed_inputs = params.fixed_inputs
        fixed_outputs = params.fixed_outputs

        def funding() -> int:
            return sum(x.satoshis for x in fixed_inputs) + sum(x.satoshis for x in r.allocated_funding_inputs)

        def spending() -> int:
            return sum(x.satoshis for x in fixed_outputs)

        def change() -> int:
            return sum(x.satoshis for x in r.change_outputs)

        def fee_func() -> int:
            return funding() - spending() - change()

        def size_func(added_funding_inputs: int = 0, added_change_outputs: int = 0) -> int:
            input_script_lengths = [x.unlocking_script_length for x in fixed_inputs] + [
                params.change_unlocking_script_length
            ] * (len(r.allocated_funding_inputs) + added_funding_inputs)

            output_script_lengths = [x.locking_script_length for x in fixed_outputs] + [
                params.change_locking_script_length
            ] * (len(r.change_outputs) + added_change_outputs)

            size = transaction_size(input_script_lengths, output_script_lengths)
            return size

        def fee_target(added_funding_inputs: int = 0, added_change_outputs: int = 0) -> int:
            size = size_func(added_funding_inputs, added_change_outputs)
            fee = math.ceil((size / 1000) * sats_per_kb)
            return fee

        fee_excess_now = 0

        def fee_excess(added_funding_inputs: int = 0, added_change_outputs: int = 0) -> int:
            nonlocal fee_excess_now
            fe = funding() - spending() - change() - fee_target(added_funding_inputs, added_change_outputs)
            if added_funding_inputs == 0 and added_change_outputs == 0:
                fee_excess_now = fe
            return fe

        fee_excess()  # initialize fee_excess_now

        target_net_count = params.target_net_count

        def net_change_count() -> int:
            return len(r.change_outputs) - len(r.allocated_funding_inputs)

        def add_output_to_balance_new_input() -> bool:
            # If we assume target_net_count is always defined (default 0)
            return net_change_count() - 1 < target_net_count

        def release_allocated_funding_inputs() -> None:
            nonlocal fee_excess_now
            while len(r.allocated_funding_inputs) > 0:
                i = r.allocated_funding_inputs.pop()
                release_funding_input(i.output_id)
            fee_excess()

        # Initial population of change outputs
        while (target_net_count > net_change_count()) or (len(r.change_outputs) == 0 and fee_excess() > 0):
            r.change_outputs.append(
                GenerateChangeSdkChangeOutput(
                    satoshis=(
                        params.change_first_satoshis if len(r.change_outputs) == 0 else params.change_initial_satoshis
                    ),
                    locking_script_length=params.change_locking_script_length,
                )
            )

        def fund_transaction() -> None:
            removing_outputs = False

            def attempt_to_fund_transaction() -> bool:
                if fee_excess() > 0:
                    return True

                exact_satoshis: int | None = None
                if target_net_count == 0 and len(r.change_outputs) == 0:
                    exact_satoshis = -fee_excess(1)

                ao = 1 if add_output_to_balance_new_input() else 0
                fee_excess_val = fee_excess(1, ao)
                target_satoshis = -fee_excess_val + (2 * params.change_initial_satoshis if ao == 1 else 0)

                allocated_input = allocate_funding_input(target_satoshis, exact_satoshis)

                if not allocated_input:
                    return False

                r.allocated_funding_inputs.append(allocated_input)

                if not removing_outputs and fee_excess() > 0:
                    if ao == 1 or len(r.change_outputs) == 0:
                        r.change_outputs.append(
                            GenerateChangeSdkChangeOutput(
                                satoshis=min(
                                    fee_excess(),
                                    (
                                        params.change_first_satoshis
                                        if len(r.change_outputs) == 0
                                        else params.change_initial_satoshis
                                    ),
                                ),
                                locking_script_length=params.change_locking_script_length,
                            )
                        )
                return True

            while True:
                # Starvation loop
                release_allocated_funding_inputs()

                while fee_excess() < 0:
                    ok = attempt_to_fund_transaction()
                    if not ok:
                        break

                if fee_excess() >= 0 or len(r.change_outputs) == 0:
                    break

                removing_outputs = True
                while len(r.change_outputs) > 0 and fee_excess() < 0:
                    r.change_outputs.pop()

                if fee_excess() < 0:
                    break

                # Optimization loop (churn reduction)
                funding_inputs = list(r.allocated_funding_inputs)
                while len(funding_inputs) > 1 and len(r.change_outputs) > 1:
                    last_output = r.change_outputs[-1]
                    # find index where satoshis <= lastOutput.satoshis
                    idx = -1
                    for i, fi in enumerate(funding_inputs):
                        if fi.satoshis <= last_output.satoshis:
                            idx = i
                            break

                    if idx < 0:
                        break
                    r.change_outputs.pop()
                    funding_inputs.pop(idx)

        fund_transaction()

        if fee_excess() < 0 and "has_max_possible_output" in vgcpr:
            idx = vgcpr["hasMaxPossibleOutput"]
            if fixed_outputs[idx].satoshis != MAX_POSSIBLE_SATOSHIS:
                raise InternalError()

            fixed_outputs[idx].satoshis += fee_excess()
            r.max_possible_satoshis_adjustment = {"fixedOutputIndex": idx, "satoshis": fixed_outputs[idx].satoshis}

        if fee_excess() < 0:
            release_allocated_funding_inputs()
            raise InsufficientFundsError(spending() + fee_target(), -fee_excess_now)

        # If needed, seek funding to avoid overspending on fees without a change output to recapture it.
        if len(r.change_outputs) == 0 and fee_excess_now > 0:
            release_allocated_funding_inputs()
            raise InsufficientFundsError(spending() + fee_target(), params.change_first_satoshis)

        while len(r.change_outputs) > 0 and fee_excess_now > 0:
            if len(r.change_outputs) == 1:
                r.change_outputs[0].satoshis += fee_excess_now
                fee_excess_now = 0
            elif r.change_outputs[0].satoshis < params.change_initial_satoshis:
                sats = min(fee_excess_now, params.change_initial_satoshis - r.change_outputs[0].satoshis)
                fee_excess_now -= sats
                r.change_outputs[0].satoshis += sats
            else:
                sats = max(1, math.floor((rand(2500, 5000) / 10000) * fee_excess_now))
                fee_excess_now -= sats
                index = rand(0, len(r.change_outputs) - 1)
                r.change_outputs[index].satoshis += sats

        r.size = size_func()
        r.fee = fee_func()
        r.sats_per_kb = sats_per_kb

        # Validate result
        validate_generate_change_sdk_result(params, r)

        return r

    except Exception as e:
        if isinstance(e, InsufficientFundsError):
            raise e
        raise e


def validate_generate_change_sdk_result(
    params: GenerateChangeSdkParams, r: GenerateChangeSdkResult
) -> tuple[bool, str]:
    ok = True
    log_msg = ""
    sum_in = sum(x.satoshis for x in params.fixed_inputs) + sum(x.satoshis for x in r.allocated_funding_inputs)
    sum_out = sum(x.satoshis for x in params.fixed_outputs) + sum(x.satoshis for x in r.change_outputs)

    if r.fee < 0:
        log_msg += f"basic fee error {r.fee};"
        ok = False

    fee_paid = sum_in - sum_out
    if fee_paid != r.fee:
        log_msg += f"exact fee error {fee_paid} !== {r.fee};"
        ok = False

    fee_required = math.ceil((r.size / 1000) * r.sats_per_kb)
    if fee_required != r.fee:
        log_msg += f"required fee error {fee_required} !== {r.fee};"
        ok = False

    if not ok:
        raise InternalError(f"generateChangeSdk error: {log_msg}")

    return ok, log_msg
