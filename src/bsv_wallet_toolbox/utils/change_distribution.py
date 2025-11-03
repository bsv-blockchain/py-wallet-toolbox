"""Change output distribution utility (GO port)."""

from __future__ import annotations

from collections.abc import Callable, Iterable


class ChangeDistribution:
    def __init__(self, initial_value: int, randomizer: Callable[[int], int]) -> None:
        self.initial_value = int(initial_value)
        self.randomizer = randomizer

    def distribute(self, count: int, amount: int) -> Iterable[int]:
        count = int(count)
        amount = int(amount)
        if count <= 0 or amount <= 0:
            return []

        # Equal baseline and saturation threshold
        saturation_threshold = count * self.initial_value
        if count == 1:
            return [amount]
        if amount == saturation_threshold:
            return [self.initial_value] * count
        if amount > saturation_threshold:
            # saturatedRandomDistribution
            base = amount // count
            remainder = amount % count
            # initial distribution: [base+remainder, base, base, ...]
            dist = [base + remainder] + [base] * (count - 1)
            # random noise per output: range = current - initialValue
            noise: list[int] = []
            for current in dist:
                random_range = current - self.initial_value
                noise.append(self.randomizer(random_range) if random_range > 0 else 0)
            # apply noise using reverse index
            result: list[int] = []
            for i, current in enumerate(dist):
                reverse_index = count - i - 1
                v = current - noise[i] + noise[reverse_index]
                result.append(v)
            return result
        else:
            # notSaturatedDistribution
            saturated_outputs = count - 1
            value_of_sat = saturated_outputs * self.initial_value
            if amount > value_of_sat:
                first = amount - value_of_sat
                return [first] + [self.initial_value] * saturated_outputs
            raise ValueError(
                f"Cannot distribute change outputs among given outputs (count: {count}) for given amount ({amount})"
            )
