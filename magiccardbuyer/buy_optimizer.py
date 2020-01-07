"""Optimizer to solve the cheapest solution for buying goods from vendors.

In particular, we are looking to solve the problem where we want a certain number of each distinct
type of good. Each good is available from some number of different vendors, each of whom has some
quantity for offer at some price. Furthermore, and this is the tricky part, each vendor is unwilling
to sell to us unless we meet a minimum threshold for our entire purchase from that vendor. (All of
these quantities are integers.)

If it weren't for the minimum threshold, we would just greedily buy from the cheapest vendor for
each good. In order to satisfy the minimum threshold problem, though, we need to solve this as a
mixed-integer linear programming problem, minimizing an objective that is linear in our variables,
and with constraints that are linear as well. (You'll see below that we come up with a clever hack,
suggested to me by Michael Kaye, defining a 0 or 1 variable for whether we purchase from a vendor,
in order to linearize the minimum threshold requirement.)

We use Google's OR Tools library to solve the MILP problem once we have expressed it.
"""
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Any, TypeVar, Callable

from ortools.linear_solver import pywraplp

S = TypeVar('S')
T = TypeVar('T')


def group_to_dict(input_list: List[T], by: Callable[[T], S]) -> Dict[S, T]:
    """Helper method for turning a list into a dict, grouping by a provided function.

    The equivalent of Java or Kotlin's groupBy."""
    output = defaultdict(list)
    for item in input_list:
        output[by(item)].append(item)
    return {key: value for key, value in output.items()}


@dataclass
class PurchaseOption:
    """A single option for purchasing a particular good from a particular vendor.

    Goods can be anything but must have a string repr and an equals, and be hashable (Strings, dataclasses...
    Note that if you use a dataclass it must be hashable - i.e., frozen or unsafe hash.)

    Vendors are correlated by their string name."""
    good: Any
    vendor: str
    availableQuantity: int
    price: int

    """This unique key identifies the option. It must not collide with any other option in the problem."""

    def key(self):
        return f"{self.vendor}_{self.good}"


@dataclass
class VendorProblem:
    """An optimization problem to be solved.

    minimumRequiredPurchase -- if a vendor's name is not present in this dict, they have no minimum purchase."""
    goodQuantitiesSought: Dict[Any, int]
    purchaseOptions: List[PurchaseOption]

    minimumRequiredPurchaseByVendor: Dict[str, int]

    optionsByGood: Dict[str, PurchaseOption] = field(init=False)
    optionsByVendor: Dict[str, PurchaseOption] = field(init=False)

    def __post_init__(self):
        self.optionsByGood = group_to_dict(self.purchaseOptions, lambda option: option.good)
        self.optionsByVendor = group_to_dict(self.purchaseOptions, lambda option: option.vendor)


@dataclass
class PurchaseToMake:
    """As part of a result, how many of the good should be purchased from this option."""
    quantity: int
    option: PurchaseOption


@dataclass
class VendorSolution:
    """A total solution.

    purchasesToMake -- this contains only purchases that should be made; i.e., quantity > 0.
    totalCost -- this is theoretically derivable from purchasesToMake but is here for convenience."""
    purchasesToMake: List[PurchaseToMake]
    totalCost: int


class UnsolvableError(Exception):
    def __init__(self, message):
        super().__init__(message)


class BuyOptimizer:
    def __init__(self):
        self.verbose = True
        # This large number is used to enforce the "buy flag". If you're ever trying to buy
        # more total goods than this, the optimizer will break down.
        self.LARGE_NUM = 1000000

    def write(self, message):
        if self.verbose:
            sys.stderr.write(message)

    def solve(self, problem: VendorProblem) -> VendorSolution:
        solver = pywraplp.Solver('SolveIntegerProblem',
                                 pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

        self.write("Initializing quantity variables...\n")
        # A list of (variable, option) pairs.
        quantity_variables = [(solver.IntVar(0, option.availableQuantity, f"{option.key()}_quantity"),
                               option) for option in problem.purchaseOptions]

        self.write("Grouping quantity variables...\n")
        variables_by_good = group_to_dict(quantity_variables, lambda v: v[1].good)
        variables_by_vendor = group_to_dict(quantity_variables, lambda v: v[1].vendor)

        # We define a variable for each vendor that is whether we are purchasing anything for that vendor: the
        # "buy flag". The existence of this flag lets us use the "hacky" constraints below to maintain linearity
        # of the problem.
        self.write("Initializing buy flags...\n")
        buy_flags_by_vendor = {vendor: solver.IntVar(0, 1, f"buyFlag_{vendor}")
                               for vendor in variables_by_vendor.keys()}

        self.write("Defining amount constraints...\n")
        # We need the desired amount of each good.
        for (good, quantity) in problem.goodQuantitiesSought.items():
            desired_amount = solver.Constraint(quantity, quantity)
            if good not in variables_by_good:
                raise UnsolvableError(f"Desire {good} but it is unavailable")
            for (variable, option) in variables_by_good[good]:
                desired_amount.SetCoefficient(variable, 1)

        self.write("Defining buy flag constraints...\n")
        # Don't buy anything from a merchant unless its flag is set.
        # (quantity1 + quantity2 + ....) - (LARGE_NUM) * buyFlag <= 0
        # This constraint is a bit of a hack in order to maintain the linearity of the problem. We pick an arbitrarily
        # large coefficient on the buy flag.
        for vendor in buy_flags_by_vendor.keys():
            buy_anything = solver.Constraint(-solver.infinity(), 0)
            buy_anything.SetCoefficient(buy_flags_by_vendor[vendor], -self.LARGE_NUM)
            for variable in variables_by_vendor[vendor]:
                buy_anything.SetCoefficient(variable[0], 1)

        self.write("Defining minimum spend constraints...\n")
        # If we do buy anything from a merchant, we need to spend at least the minimum amount.
        # (MINIMUM_SPEND) * buyFlag - quantity1 * cost1 - quantity2 * cost2 - ... <= 0
        # Here is where the buyFlag lets us maintain linearity.
        for vendor in buy_flags_by_vendor.keys():
            if vendor in problem.minimumRequiredPurchaseByVendor:
                minimum_spend = solver.Constraint(-solver.infinity(), 0)
                minimum_spend.SetCoefficient(buy_flags_by_vendor[vendor],
                                             problem.minimumRequiredPurchaseByVendor[vendor])
                for variable in variables_by_vendor[vendor]:
                    minimum_spend.SetCoefficient(variable[0], -variable[1].price)

        self.write("Defining objective...\n")
        total_cost = solver.Objective()
        for variable in quantity_variables:
            total_cost.SetCoefficient(variable[0], variable[1].price)
        total_cost.SetMinimization()

        self.write(f"Solving for {len(quantity_variables) + len(buy_flags_by_vendor)} variables...\n")
        result_status = solver.Solve()
        self.write("Solved.\n")
        if result_status != pywraplp.Solver.OPTIMAL:
            raise UnsolvableError(f"Vendor problem was not mathematically solveable; returned status {result_status}")

        if not solver.VerifySolution(1e-7, True):
            raise UnsolvableError("Solution could not be verified as legitimate")

        purchases_to_make = [PurchaseToMake(variable[0].solution_value(), variable[1])
                             for variable in quantity_variables if variable[0].solution_value() > 0]
        total_cost = solver.Objective().Value()
        return VendorSolution(purchases_to_make, total_cost)
