package com.lindsaylevine.magiccardbuyer.optimizer

import org.chocosolver.solver.Model
import org.chocosolver.solver.Solution
import org.chocosolver.solver.variables.IntVar

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
        private const val LARGE_NUMBER = 1_000_000
    }

    fun <T> solve(problem: VendorProblem<T>): VendorSolution<T> {
        val model = Model()

        val variablesForOptions = problem.purchaseOptions.map { option ->
            val variable = model.intVar(0, option.availableQuantity)
            VariableAndOption(variable, option)
        }

        val variablesByGood = variablesForOptions.groupBy { it.option.good }
        val variablesByVendor = variablesForOptions.groupBy { it.option.vendorName }

        //We define a variable for each vendor that is whether we are purchasing anything for that vendor: the
        // "buy flag". The existence of this flag lets us use the "hacky" constraints below to maintain linearity
        // of the problem.
        val buyFlagsByVendor: Map<String, IntVar> = variablesByVendor.keys.associate { vendorName ->
            vendorName to model.intVar(0, 1)
        }

        // We need the desired amount of each good.
        problem.goodQuantitiesSought.forEach { (good, quantity) ->
            val variables = variablesByGood[good] ?: throw UnsolvableException("Desire $good but it is unavailable")
            val coefficients = variables.map { 1 }.toIntArray()
            model.scalar(variables.map { it.variable }.toTypedArray(),
                    coefficients,
                    "=",
                    quantity)
                    .post()
        }

        variablesByVendor.forEach { (vendorName, variables) ->
            val buyFlag: IntVar = buyFlagsByVendor[vendorName]
                    ?: throw IllegalStateException("Missing buy flag for $vendorName")

            val vendorVars = variables.map { it.variable }.toList()

            // Don't buy anything from a merchant unless its flag is set.
            // (quantity1 + quantity2 + ....) - (LARGE_NUM) * buyFlag <= 0
            // This constraint is a bit of a hack in order to maintain the linearity of the problem. We pick an arbitrarily
            // large coefficient on the buy flag.
            model.scalar(vendorVars.plusElement(buyFlag).toTypedArray(),
                    (variables.map { 1 } + (-LARGE_NUMBER)).toIntArray(),
                    "<=",
                    0)
                    .post()

            // If we do buy anything from a merchant, we need to spend at least the minimum amount.
            // quantity1 * cost 1 + quantity2 * cost 2 + .... - MINIMUM_SPEND * buyFlag >= 0
            // Here is where the buyFlag lets us maintain linearity.
            model.scalar(vendorVars.plusElement(buyFlag).toTypedArray(),
                    (variables.map { it.option.price } + (-problem.minimumRequiredPurchase)).toIntArray(),
                    ">=",
                    0)
                    .post()
        }

        val totalCost = model.intVar(0, IntVar.MAX_INT_BOUND)
        model.scalar(variablesForOptions.map { it.variable }.toTypedArray(),
                variablesForOptions.map { it.option.price }.toIntArray(),
                "=",
                totalCost)
                .post()

        model.setObjective(Model.MINIMIZE, totalCost)

        val solution = Solution(model)
        var anySolutionFound = false

        // Each solution advances another step towards the optimization - we should be at the
        // most optimal when there is not another solution.
        model.solver.limitTime(10_000)

        while (model.solver.solve()) {
            solution.record()
            anySolutionFound = true
        }

        if (!anySolutionFound) {
            throw UnsolvableException("No solution could be found")
        }

        val purchasesToMake = variablesForOptions.filter { solution.getIntVal(it.variable) > 0 }
                .map { PurchaseToMake(solution.getIntVal(it.variable), it.option) }
        return VendorSolution(purchasesToMake)
    }
}

private data class VariableAndOption<T>(val variable: IntVar, val option: PurchaseOption<T>)