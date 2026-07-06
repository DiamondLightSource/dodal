from collections.abc import Callable
from dataclasses import dataclass

import pytest


@dataclass(frozen=True)
class OperatorInversionPairing:
    """Represents a pair of mutually reciprocal maths functions, with unique mappings of input to output.
        Useful for sanity check behavioural tests above the unit level but below integration level.
        A typical use case is to ensure that after two mutually cancelling numerical operations,
         an original input number is restored.  This helps tests flag whenever one function breaks,
         for example - owing to a typo or incorrect or inverted multiplication factor.
         ( Yes there are even numbers of self-cancelling mistakes which can still hide bugs but
           hopefully the individual functions, functional tests flush those out ).

    Attributes:
        unary_op: A unary operation mathematical function (specifically with unique one-to-one mapping).
        inverse_op: The inverse unary operation.
    """

    unary_op: Callable[[float], float]
    inverse_op: Callable[[float], float]

    def _composed_operator(self, x: float) -> float:
        """Applies both the unary operation followed by the inverse operation on a numerical input.
            On, for example, the happy path of a test, this round-trip can be expected to result in the original value x.
            Internal method.

        Args:
            x (float): Any numerical argument suitable for the unary operations under test.

        Returns:
            float: The result from nested application of first the unary operation and then its inverse on x.
        """
        _f_of_x = self.unary_op(x)
        return self.inverse_op(_f_of_x)

    def composed_operator_is_consistent_with_identity_operator(
        self, probe_x: float
    ) -> bool:
        """Used in tests when verifying that a pair of functions compose to act like the identity operator.
            Namely that for f, g where g is the inverse of f, asserts that g(f(x)) is consistent with x to good approximation.

        Args:
            probe_x (float): Any numerical argument suitable for the unary operations under test.
        """
        _round_trip_net_effect = self._composed_operator(probe_x)
        return _round_trip_net_effect == pytest.approx(probe_x)
