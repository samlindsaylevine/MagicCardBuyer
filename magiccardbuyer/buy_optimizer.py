from dataclasses import 
from typing import List, Dict
from ortools.linear_solver import pywraplp

@dataclass(frozen = true)
class VendorProblem:
	goodQuantitiesSought: Dict[str, int]
	purchaseOptions: List[PurchaseOption]
	minimumRequiredPurchase: int

@dataclass(frozen = true)
class PurchaseOption:
	good: str
	vendor: str
	availableQuantity: int 
	price: int

class BuyOptimizer:
	def __init__(self):
		self.LARGE_NUM = 1000000
		self.MINIMUM_SPEND = 200

	def solve(self, problem: VendorProblem):
		solver = pywraplp.Solver('SolveIntegerProblem',
			pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

		buyFlag = solver.IntVar(0.0, 1.0, 'buyMerchant1')
		merchant1Quantity1 = solver.IntVar(0.0, 100.0, 'merchant1Quantity1')
		merchant1Quantity2 = solver.IntVar(0.0, 100.0, 'merchant1Quantity2')

		merchant1Cost1 = 112
		merchant1Cost2 = 95

		# Don't buy anything from merchant 1 unless its flag is set.
		# quantity1 + quantity2 - (LARGE_NUM) * buyFlag <= 0
		buyAnything = solver.Constraint(-solver.infinity(), 0)
		buyAnything.SetCoefficient(merchant1Quantity1, 1)
		buyAnything.SetCoefficient(merchant1Quantity2, 1)
		buyAnything.SetCoefficient(buyFlag, -self.LARGE_NUM)

		# If we do buy from merchant 1, we need to spend at least the minimum
		# amount.
		# (MINIMUM_SPEND) * buyFlag - quantity1 * cost1 - quantity2 * cost2 <= 0
		minimumSpend = solver.Constraint(-solver.infinity(), 0)
		buyAnything.SetCoefficient(merchant1Quantity1, -merchant1Cost1)
		buyAnything.SetCoefficient(merchant1Quantity2, -merchant1Cost2)
		buyAnything.SetCoefficient(buyFlag, self.MINIMUM_SPEND)

		# We want to buy 1 of each good.
		good1 = solver.Constraint(1, 1)
		good1.SetCoefficient(merchant1Quantity1, 1)
		good2 = solver.Constraint(1, 1)
		good2.SetCoefficient(merchant1Quantity2, 1)

		cost = solver.Objective()
		cost.SetCoefficient(merchant1Quantity1, merchant1Cost1)
		cost.SetCoefficient(merchant1Quantity2, merchant1Cost2)
		cost.SetMinimization()

		result_status = solver.Solve()
		print('Number of variables =', solver.NumVariables())
		print('Number of constraints =', solver.NumConstraints())
		print("Solution completed")
		print(f"Result status: {result_status}")
		print(f"Verify solution: {solver.VerifySolution(1e-7, True)}")

		print(f"{merchant1Quantity1.name()} = {merchant1Quantity1.solution_value()}")
		print(f"{merchant1Quantity2.name()} = {merchant1Quantity2.solution_value()}")
		print(f"{buyFlag.name()} = {buyFlag.solution_value()}")
		print(f"total cost: {solver.Objective().Value()}")



if __name__ == "__main__":

	BuyOptimizer().solve("problem")