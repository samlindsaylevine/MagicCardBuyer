package com.lindsaylevine.magiccardbuyer.optimizer

import com.google.ortools.Loader
import com.google.ortools.linearsolver.MPSolver
import com.google.ortools.linearsolver.MPVariable

/**
 * Optimizer to solve the cheapest solution for buying goods from vendors.
 *
 * In particular, we are looking to solve the problem where we want a certain number of each distinct
 * type of good. Each good is available from some number of different vendors, each of whom has some
 * quantity for offer at some price. Furthermore, and this is the tricky part, each vendor is unwilling
 * to sell to us unless we meet a minimum threshold for our entire purchase from that vendor. (All of
 * these quantities are integers.)
 *
 * If it weren't for the minimum threshold, we would just greedily buy from the cheapest vendor for
 * each good. In order to satisfy the minimum threshold problem, though, we need to solve this as a
 * mixed-integer linear programming problem, minimizing an objective that is linear in our variables,
 * and with constraints that are linear as well. (You'll see below that we come up with a clever hack,
 * suggested to me by Michael Kaye, defining a 0 or 1 variable for whether we purchase from a vendor,
 * in order to linearize the minimum threshold requirement.)
 *
 * We use Google's OR Tools library to solve the MILP problem once we have expressed it.
 */
class BuyOptimizer {

    companion object {
        /**
         * This large number is used to enforce the "buy flag". If you're ever trying to buy
         * more total goods than this, the optimizer will break down.
         */
        private const val LARGE_NUMBER = 1_000_000.0
    }

    init {
        Loader.loadNativeLibraries()
    }

    fun <T> solve(problem: VendorProblem<T>): VendorSolution<T> {
        val solver = MPSolver.createSolver(MPSolver.OptimizationProblemType.CBC_MIXED_INTEGER_PROGRAMMING.name)

        val variablesForOptions = problem.purchaseOptions.map { option ->
            val variable = solver.makeIntVar(0.0, option.availableQuantity.toDouble(), option.key)
            VariableAndOption(variable, option)
        }

        val variablesByGood = variablesForOptions.groupBy { it.option.good }
        val variablesByVendor = variablesForOptions.groupBy { it.option.vendorName }

        //We define a variable for each vendor that is whether we are purchasing anything for that vendor: the
        // "buy flag". The existence of this flag lets us use the "hacky" constraints below to maintain linearity
        // of the problem.
        val buyFlagsByVendor: Map<String, MPVariable> =
            variablesByVendor.keys.associateWith { vendorName -> solver.makeIntVar(0.0, 1.0, "buy_flag_$vendorName") }

        // We need the desired amount of each good.
        problem.goodQuantitiesSought.forEach { (good, quantity) ->
            val variables = variablesByGood[good] ?: throw UnsolvableException("Desire $good but it is unavailable")
            val totalAmountConstraint = solver.makeConstraint(quantity.toDouble(), quantity.toDouble())
            variables.forEach { totalAmountConstraint.setCoefficient(it.variable, 1.0) }
        }

        variablesByVendor.forEach { (vendorName, variables) ->
            val buyFlag: MPVariable = buyFlagsByVendor[vendorName]
                    ?: throw IllegalStateException("Missing buy flag for $vendorName")

            val vendorVars = variables.map { it.variable }

            // Don't buy anything from a merchant unless its flag is set.
            // (quantity1 + quantity2 + ....) - (LARGE_NUM) * buyFlag <= 0
            // This constraint is a bit of a hack in order to maintain the linearity of the problem. We pick an arbitrarily
            // large coefficient on the buy flag.
            val buyAnything = solver.makeConstraint(-MPSolver.infinity(), 0.0)
            buyAnything.setCoefficient(buyFlag, -LARGE_NUMBER)
            vendorVars.forEach { buyAnything.setCoefficient(it, 1.0) }

            // If we do buy anything from a merchant, we need to spend at least the minimum amount.
            // quantity1 * cost 1 + quantity2 * cost 2 + .... - MINIMUM_SPEND * buyFlag >= 0
            // Here is where the buyFlag lets us maintain linearity.
            val minimumSpend = solver.makeConstraint(-MPSolver.infinity(), 0.0)
            minimumSpend.setCoefficient(buyFlag, problem.minimumRequiredPurchase.toDouble())
            variables.forEach { minimumSpend.setCoefficient(it.variable,-it.option.price.toDouble()) }
        }

        val totalCost = solver.objective()
        variablesForOptions.forEach { (variable, option) ->
            totalCost.setCoefficient(variable, option.price.toDouble())
        }
        totalCost.setMinimization()

        val resultStatus = solver.solve()

        if (resultStatus != MPSolver.ResultStatus.OPTIMAL) {
            throw UnsolvableException("Vendor problem was not mathematically solveable; returned status $resultStatus")
        }

        if (!solver.verifySolution(1e-7, true)) {
            throw UnsolvableException("Solution could not be verified as legitimate")
        }

        val purchasesToMake = variablesForOptions.filter { it.variable.solutionValue() >0 }
                .map { PurchaseToMake(it.variable.solutionValue().toInt(), it.option) }
        return VendorSolution(purchasesToMake)
    }
}

private data class VariableAndOption<T>(val variable: MPVariable, val option: PurchaseOption<T>)