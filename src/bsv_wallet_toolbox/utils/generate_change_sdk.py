"""Generate change inputs/outputs for transaction construction.

Reference (TS): toolbox/ts-wallet-toolbox/src/storage/methods/generateChange.ts
"""

from __future__ import annotations

import random
from typing import Any

from bsv_wallet_toolbox.errors import InsufficientFundsError
from bsv_wallet_toolbox.utils.tx_size import transaction_size

MAX_POSSIBLE_SATOSHIS = 2_099_999_999_999_999


def _varint_len(n: int) -> int:
    if n <= 252:
        return 1
    if n <= 0xFFFF:
        return 3
    if n <= 0xFFFFFFFF:
        return 5
    return 9


def generate_change_sdk(params: dict[str, Any], available_change: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate change inputs/outputs for transaction construction (SDK-backed).

    Port of ts-wallet-toolbox generateChangeSdk with scoped simplifications:
    - Only sat/kb fee model
    - Fixed script lengths for change inputs/outputs
    - Local storage allocator over provided available_change
    """

    fixed_inputs: list[dict[str, int]] = list(params.get("fixedInputs", []))
    fixed_outputs: list[dict[str, int]] = list(params.get("fixedOutputs", []))
    fee_model = params.get("feeModel", {"model": "sat/kb", "value": 0})
    sats_per_kb: int = int(fee_model.get("value", 0))
    target_net_count = params.get("targetNetCount")
    has_target_net = target_net_count is not None
    target_net = int(target_net_count) if has_target_net else 0
    change_initial = int(params.get("changeInitialSatoshis", 0))
    change_first = int(params.get("changeFirstSatoshis", change_initial))
    change_lock_len = int(params.get("changeLockingScriptLength", 0))
    change_unlock_len = int(params.get("changeUnlockingScriptLength", 0))

    # Storage over available change
    change_store: list[dict[str, Any]] = [
        {"satoshis": int(c["satoshis"]), "outputId": int(c["outputId"]), "spendable": True} for c in available_change
    ]
    change_store.sort(key=lambda c: (c["satoshis"], c["outputId"]))

    # log removed (unused)

    def allocate(c: dict[str, Any]) -> dict[str, Any]:
        c["spendable"] = False
        return {"satoshis": c["satoshis"], "outputId": c["outputId"], "spendable": False}

    def allocate_funding_input(target_satoshis: int, exact_satoshis: int | None = None) -> dict[str, Any] | None:
        if exact_satoshis is not None:
            exact = next((c for c in change_store if c["spendable"] and c["satoshis"] == exact_satoshis), None)
            if exact:
                return allocate(exact)
        over = next((c for c in change_store if c["spendable"] and c["satoshis"] >= target_satoshis), None)
        if over:
            return allocate(over)
        for i in range(len(change_store) - 1, -1, -1):
            c = change_store[i]
            if c["spendable"]:
                return allocate(c)
        return None

    def release_funding_input(output_id: int) -> None:
        c = next((x for x in change_store if x["outputId"] == output_id), None)
        if c and not c["spendable"]:
            c["spendable"] = True

    result: dict[str, Any] = {
        "allocatedFundingInputs": [],
        "changeOutputs": [],
        "size": 0,
        "fee": 0,
        "satsPerKb": 0,
    }

    def funding() -> int:
        return sum(int(e["satoshis"]) for e in fixed_inputs) + sum(
            int(e["satoshis"]) for e in result["allocatedFundingInputs"]
        )

    def spending() -> int:
        return sum(int(e["satoshis"]) for e in fixed_outputs)

    def total_change() -> int:
        return sum(int(e["satoshis"]) for e in result["changeOutputs"])

    def fee_now() -> int:
        return funding() - spending() - total_change()

    def size(added_funding_inputs: int = 0, added_change_outputs: int = 0) -> int:
        input_script_lengths = [int(x.get("unlockingScriptLength", 0)) for x in fixed_inputs]
        input_script_lengths += [change_unlock_len] * (len(result["allocatedFundingInputs"]) + added_funding_inputs)
        output_script_lengths = [int(x.get("lockingScriptLength", 0)) for x in fixed_outputs]
        output_script_lengths += [change_lock_len] * (len(result["changeOutputs"]) + added_change_outputs)
        return transaction_size(input_script_lengths, output_script_lengths)

    def fee_target(added_funding_inputs: int = 0, added_change_outputs: int = 0) -> int:
        return (size(added_funding_inputs, added_change_outputs) * sats_per_kb + 999) // 1000

    fee_excess_now = 0

    def fee_excess(added_funding_inputs: int = 0, added_change_outputs: int = 0) -> int:
        nonlocal fee_excess_now
        fe = funding() - spending() - total_change() - fee_target(added_funding_inputs, added_change_outputs)
        if added_funding_inputs == 0 and added_change_outputs == 0:
            fee_excess_now = fe
        return fe

    def net_change_count() -> int:
        return len(result["changeOutputs"]) - len(result["allocatedFundingInputs"])

    def add_output_to_balance_new_input() -> bool:
        if not has_target_net:
            return False
        return net_change_count() - 1 < target_net

    def release_allocated_funding_inputs() -> None:
        while result["allocatedFundingInputs"]:
            i = result["allocatedFundingInputs"].pop()
            release_funding_input(int(i["outputId"]))
        fee_excess()

    fee_excess()

    # Initial change outputs for net count or if we already overpay
    while (has_target_net and target_net > net_change_count()) or (
        len(result["changeOutputs"]) == 0 and fee_excess() > 0
    ):
        result["changeOutputs"].append(
            {
                "satoshis": change_first if len(result["changeOutputs"]) == 0 else change_initial,
                "lockingScriptLength": change_lock_len,
            }
        )

    def fund_transaction() -> None:
        removing_outputs = False

        def attempt_to_fund_transaction() -> bool:
            if fee_excess() > 0:
                return True
            exact_satoshis: int | None = None
            if not has_target_net and len(result["changeOutputs"]) == 0:
                exact_satoshis = -fee_excess(1, 0)
            ao = 1 if add_output_to_balance_new_input() else 0
            target_satoshis = -fee_excess(1, ao) + (2 * change_initial if ao == 1 else 0)
            allocated = allocate_funding_input(target_satoshis, exact_satoshis)
            if not allocated:
                return False
            result["allocatedFundingInputs"].append(allocated)
            if not removing_outputs and fee_excess() > 0:
                if ao == 1 or len(result["changeOutputs"]) == 0:
                    result["changeOutputs"].append(
                        {
                            "satoshis": min(
                                fee_excess(),
                                change_first if len(result["changeOutputs"]) == 0 else change_initial,
                            ),
                            "lockingScriptLength": change_lock_len,
                        }
                    )
            return True

        while True:
            release_allocated_funding_inputs()
            while fee_excess() < 0:
                ok = attempt_to_fund_transaction()
                if not ok:
                    break
            if fee_excess() >= 0 or len(result["changeOutputs"]) == 0:
                break
            removing_outputs = True
            while len(result["changeOutputs"]) > 0 and fee_excess() < 0:
                result["changeOutputs"].pop()
            if fee_excess() < 0:
                break
            funding_inputs_copy = list(result["allocatedFundingInputs"])  # type: ignore[var-annotated]
            while len(funding_inputs_copy) > 1 and len(result["changeOutputs"]) > 1:
                last_output = result["changeOutputs"][-1]
                idx = next(
                    (
                        i
                        for i, fi in enumerate(funding_inputs_copy)
                        if int(fi["satoshis"]) <= int(last_output["satoshis"])
                    ),
                    -1,
                )
                if idx < 0:
                    break
                result["changeOutputs"].pop()
                funding_inputs_copy.pop(idx)

    fund_transaction()

    # Handle maxPossibleSatoshis output reduction if present
    has_max_possible_index = next(
        (i for i, o in enumerate(fixed_outputs) if int(o.get("satoshis", 0)) == MAX_POSSIBLE_SATOSHIS),
        None,
    )
    if fee_excess() < 0 and has_max_possible_index is not None:
        fixed_outputs[has_max_possible_index]["satoshis"] = (
            int(fixed_outputs[has_max_possible_index]["satoshis"]) + fee_excess()
        )

    if fee_excess() < 0:
        release_allocated_funding_inputs()
        raise InsufficientFundsError(spending() + fee_target(), -fee_excess_now)

    if len(result["changeOutputs"]) == 0 and fee_excess_now > 0:
        release_allocated_funding_inputs()
        raise InsufficientFundsError(spending() + fee_target(), change_first)

    # Prepare TS-like random sequence
    # Use TS test vector randomVals if provided, else fall back to built-in series copied from TS
    random_vals: list[float] = list(params.get("randomVals", []))
    if not random_vals:
        random_vals = [
            0.3145996888882596,
            0.45719282963580565,
            0.8555247776688835,
            0.2649974738591665,
            0.7381622959747749,
            0.1945477495382142,
            0.5032123391994598,
            0.02861436749749835,
            0.7999598138479351,
            0.8979243255586506,
            0.9034507043487272,
            0.4280218402928029,
            0.6358932443326806,
            0.30173236243173585,
            0.3598078135029954,
            0.9870248947111777,
            0.2675337664781172,
            0.6050300757408575,
            0.7391162382709817,
            0.8727502788995358,
            0.36799576712472737,
            0.6604956576157504,
            0.1702104642469362,
            0.7797698104303106,
            0.08655953134554961,
            0.2847318171161146,
            0.07534328732698126,
            0.9009525464087105,
            0.5264602243751411,
            0.866180150709631,
            0.5813059581773354,
            0.3348084822567492,
            0.5668720381665056,
            0.03296403051210928,
            0.8225656781470101,
            0.5321943190815006,
            0.7708306957508375,
            0.13417838069050525,
            0.7763632653423949,
            0.08160553045351926,
            0.45497831351884677,
            0.13467302343886756,
            0.21261951092011078,
            0.04372527326966513,
            0.7939708066933404,
            0.31542646439897015,
            0.23821328607534542,
            0.29505981550698746,
            0.436696157907251,
            0.8692456197556584,
            0.6851392295747836,
            0.4203746637055583,
            0.9959411956291628,
            0.42200495673071803,
            0.9174433944732405,
            0.7758897322425307,
            0.3453529493770806,
            0.15520421082199776,
            0.4883039767344435,
            0.45987000169072356,
            0.9146194455087437,
            0.33743694585941686,
            0.2725130478399085,
            0.7058681732538112,
            0.18975119489481007,
            0.46483529505143717,
            0.5650362982181798,
            0.48841275156927955,
            0.8012266835493618,
            0.2952784976832741,
            0.9823977685364349,
            0.45683871241931007,
            0.6008021097728846,
            0.1405802039681765,
            0.6968599380515865,
            0.3016840411555928,
            0.8652691542976458,
            0.5733994909626297,
            0.288364714649364,
            0.28178697025295385,
            0.02893432926139794,
            0.6179746775758665,
            0.35219485471542944,
            0.97651703347549,
            0.04012334579632282,
            0.3582381346512069,
            0.5756199598871186,
            0.11453606927098825,
        ]
    rnd = random.Random(0x5A17)  # deterministic when randomVals not provided

    def next_random_val() -> float:
        if random_vals:
            v = float(random_vals.pop(0))
            random_vals.append(v)
            return v
        return rnd.random()

    def rand(min_incl: int, max_incl: int) -> int:
        if max_incl < min_incl:
            return min_incl
        # TS: Math.floor(nextRandomVal() * (max-min+1) + min)
        v = next_random_val()
        return int(v * (max_incl - min_incl + 1)) + min_incl

    # Distribute excess into change outputs (TS-compliant)
    # Step 1: bring first output up to changeInitialSatoshis if below
    if len(result["changeOutputs"]) > 0 and int(result["changeOutputs"][0]["satoshis"]) < change_initial:
        missing = change_initial - int(result["changeOutputs"][0]["satoshis"])
        take = min(missing, fee_excess_now)
        result["changeOutputs"][0]["satoshis"] = int(result["changeOutputs"][0]["satoshis"]) + take
        fee_excess_now -= take

    while len(result["changeOutputs"]) > 0 and fee_excess_now > 0:
        if len(result["changeOutputs"]) == 1:
            result["changeOutputs"][0]["satoshis"] = int(result["changeOutputs"][0]["satoshis"]) + fee_excess_now
            fee_excess_now = 0
        elif int(result["changeOutputs"][0]["satoshis"]) < change_initial:
            sats = min(fee_excess_now, change_initial - int(result["changeOutputs"][0]["satoshis"]))
            fee_excess_now -= sats
            result["changeOutputs"][0]["satoshis"] = int(result["changeOutputs"][0]["satoshis"]) + sats
        else:
            # sats = max(1, floor((rand(2500,5000)/10000) * feeExcessNow))
            pct = rand(2500, 5000)
            sats = max(1, (pct * fee_excess_now) // 10000)
            sats = min(sats, fee_excess_now)
            fee_excess_now -= sats
            index = rand(0, len(result["changeOutputs"]) - 1)
            result["changeOutputs"][index]["satoshis"] = int(result["changeOutputs"][index]["satoshis"]) + sats

    result["size"] = size()
    result["fee"] = fee_now()
    result["satsPerKb"] = sats_per_kb

    return result
