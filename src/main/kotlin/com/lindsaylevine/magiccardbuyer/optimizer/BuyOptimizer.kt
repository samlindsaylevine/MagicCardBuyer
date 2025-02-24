package com.lindsaylevine.magiccardbuyer.optimizer

import com.google.ortools.Loader
import com.google.ortools.linearsolver.MPSolver
import com.google.ortools.linearsolver.MPVariable
import com.google.ortools.sat.*

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
class BuyOptimizer : Optimizer {

    companion object {
        /**
         * This large number is used to enforce the "buy flag". If you're ever trying to buy
         * more total goods than this, the optimizer will break down.
         */
        private const val LARGE_NUMBER = 1_000_000L
    }

    init {
        Loader.loadNativeLibraries()
    }

    override fun <T> solve(problem: VendorProblem<T>): VendorSolution<T> {
        val model = CpModel()

        val variablesForOptions = problem.purchaseOptions.map { option ->
            val variable = model.newIntVar(0, option.availableQuantity.toLong(), option.key)
            VariableAndOption(variable, option)
        }

        val variablesByGood = variablesForOptions.groupBy { it.option.good }
        val variablesByVendor = variablesForOptions.groupBy { it.option.vendorName }

        //We define a variable for each vendor that is whether we are purchasing anything for that vendor: the
        // "buy flag". The existence of this flag lets us use the "hacky" constraints below to maintain linearity
        // of the problem.
        val buyFlagsByVendor: Map<String, IntVar> =
                variablesByVendor.keys.associateWith { vendorName -> model.newIntVar(0, 1, "buy_flag_$vendorName") }

        // We need the desired amount of each good.
        problem.goodQuantitiesSought.forEach { (good, quantity) ->
            val variables = variablesByGood[good] ?: throw UnsolvableException("Desire $good but it is unavailable")
            val purchasedExpression = LinearExpr.sum(variables.map { it.variable }.toTypedArray())
            model.addEquality(purchasedExpression, quantity.toLong())
        }

        variablesByVendor.forEach { (vendorName, variables) ->
            val buyFlag: IntVar = buyFlagsByVendor[vendorName]
                    ?: throw IllegalStateException("Missing buy flag for $vendorName")

            val vendorVars = variables.map { it.variable }

            // Don't buy anything from a merchant unless its flag is set.
            // (quantity1 + quantity2 + ....) - (LARGE_NUM) * buyFlag <= 0
            // This constraint is a bit of a hack in order to maintain the linearity of the problem. We pick an arbitrarily
            // large coefficient on the buy flag.
            val boughtFromThisVendorExpression = LinearExpr.weightedSum(
                (vendorVars + buyFlag).toTypedArray(),
                (List(vendorVars.size) { 1L} + (-LARGE_NUMBER)).toLongArray()
            )
            model.addLessOrEqual(boughtFromThisVendorExpression, 0)

            if (problem.minimumRequiredPurchase > 0) {
                // If we do buy anything from a merchant, we need to spend at least the minimum amount.
                // quantity1 * cost 1 + quantity2 * cost 2 + .... - MINIMUM_SPEND * buyFlag >= 0
                // Here is where the buyFlag lets us maintain linearity.
                val costFromThisVendorExpression = LinearExpr.weightedSum(
                    (vendorVars + buyFlag).toTypedArray(),
                    (variables.map { it.option.price.toLong() } + (-problem.minimumRequiredPurchase.toLong())).toLongArray()
                )
                model.addGreaterOrEqual(costFromThisVendorExpression, 0)
            }
        }

        val costPerVendorVariables = if (problem.costPerVendor > 0) buyFlagsByVendor.values else emptyList()
        val costPerVendorCoefficients = costPerVendorVariables.map { problem.costPerVendor.toLong() }

        val totalCost = LinearExpr.weightedSum(
            (variablesForOptions.map { it.variable } + costPerVendorVariables).toTypedArray(),
            (variablesForOptions.map { it.option.price.toLong() } + costPerVendorCoefficients).toLongArray()
        )

        model.minimize(totalCost)

        val numVariables = variablesForOptions.size + buyFlagsByVendor.size
        println("Solving for $numVariables variables...")
        val solver = CpSolver()
        val resultStatus = solver.solve(model)

        if (resultStatus != CpSolverStatus.OPTIMAL) {
            throw UnsolvableException("Vendor problem was not mathematically solveable; returned status $resultStatus")
        }

        val numVendors = buyFlagsByVendor.values.sumOf { solver.value(it) }
        println("Solved; solution is from ${numVendors.toInt()} vendors for estimated cost ${solver.objectiveValue()}")

        val purchasesToMake = variablesForOptions.filter { solver.value(it.variable) > 0 }
                .map { PurchaseToMake(solver.value(it.variable).toInt(), it.option) }
        return VendorSolution(purchasesToMake)
    }
}

private data class VariableAndOption<T>(val variable: IntVar, val option: PurchaseOption<T>)