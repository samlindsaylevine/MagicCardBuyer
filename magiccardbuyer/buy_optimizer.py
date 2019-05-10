from dataclasses import dataclass, field
from itertools import groupby
from typing import List, Dict, Any
from ortools.linear_solver import pywraplp

def groupToDict(inputList: List[Any], by) -> Dict[Any, Any]:
	sortedList = sorted(inputList, key=by)
	return {key: list(values) for key, values in groupby(sortedList, by)}

@dataclass
class PurchaseOption:
	good: str
	vendor: str
	availableQuantity: int 
	price: int

@dataclass
class VendorProblem:
	goodQuantitiesSought: Dict[str, int]
	purchaseOptions: List[PurchaseOption]
	minimumRequiredPurchase: int

	optionsByGood: Dict[str, PurchaseOption] = field(init = False)
	optionsByVendor: Dict[str, PurchaseOption] = field(init = False)

	def __post_init__(self):
		self.optionsByGood = groupToDict(self.purchaseOptions, lambda option: option.good)
		self.optionsByVendor = groupToDict(self.purchaseOptions, lambda option: option.vendor)

@dataclass
class PurchaseToMake:
	quantity: int
	option: PurchaseOption

@dataclass
class VendorSolution:
	purchasesToMake: List[PurchaseToMake]
	totalCost: int

class UnsolvableError(Exception):
	def __init__(self, message):
		super().__init__(message)

class BuyOptimizer:
	def __init__(self):
		self.LARGE_NUM = 1000000
		self.MINIMUM_SPEND = 200

	def solve(self, problem: VendorProblem) -> VendorSolution:
		solver = pywraplp.Solver('SolveIntegerProblem',
			pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

		# A list of (variable, option) pairs.
		quantityVariables = [(solver.IntVar(0, option.availableQuantity, f"{option.vendor}_{option.good}_quantity"),
			option) for option in problem.purchaseOptions]

		variablesByGood = groupToDict(quantityVariables, lambda variable: variable[1].good)
		variablesByVendor = groupToDict(quantityVariables, lambda variable: variable[1].vendor)

		# We define a variable for each vendor that is whether we are purchasing anything for that vendor: the
		# "buy flag". The existence of this flag lets us use the "hacky" constraints below to maintain linearity
		# of the problem.
		buyFlagsByVendor = {vendor: solver.IntVar(0, 1, f"buyFlag_{vendor}") for vendor in variablesByVendor.keys()}

		# We need the desired amount of each good.
		for (good, quantity) in problem.goodQuantitiesSought.items():
			desiredAmount = solver.Constraint(quantity, quantity)
			if good not in variablesByGood:
				raise UnsolvableError(f"Desire {good} but it is unavailable")
			for (variable, option) in variablesByGood[good]:
				desiredAmount.SetCoefficient(variable, 1)

		# Don't buy anything from a merchant unless its flag is set.
		# (quantity1 + quantity2 + ....) - (LARGE_NUM) * buyFlag <= 0
		# This constraint is a bit of a hack in order to maintain the linearity of the problem. We pick an arbitrarily
		# large coefficient on the buy flag.
		for vendor in buyFlagsByVendor.keys():
			buyAnything = solver.Constraint(-solver.infinity(), 0)
			buyAnything.SetCoefficient(buyFlagsByVendor[vendor], -self.LARGE_NUM)
			for variable in variablesByVendor[vendor]:
				buyAnything.SetCoefficient(variable[0], 1)

		# If we do buy anything from a merchant, we need to spend at least the minimum amount.
		# (MINIMUM_SPEND) * buyFlag - quantity1 * cost1 - quantity2 * cost2 - ... <= 0
		# Here is where the buyFlag lets us maintain linearity.
		for vendor in buyFlagsByVendor.keys():
			minimumSpend = solver.Constraint(-solver.infinity(), 0)
			minimumSpend.SetCoefficient(buyFlagsByVendor[vendor], problem.minimumRequiredPurchase)
			for variable in variablesByVendor[vendor]:
				minimumSpend.SetCoefficient(variable[0], -variable[1].price)

		totalCost = solver.Objective()
		for variable in quantityVariables:
			totalCost.SetCoefficient(variable[0], variable[1].price)
		totalCost.SetMinimization()

		result_status = solver.Solve()
		if (result_status != pywraplp.Solver.OPTIMAL):
			raise UnsolvableError(f"Vendor problem was not mathematically solveable; returned status {result_status}")

		if (not solver.VerifySolution(1e-7, True)):
			raise UnsolvableError("Solution could not be verified as legitimate")

		purchasesToMake = [PurchaseToMake(variable[0].solution_value(), variable[1]) 
			for variable in quantityVariables if variable[0].solution_value() > 0]
		totalCost = solver.Objective().Value()
		return VendorSolution(purchasesToMake, totalCost)
