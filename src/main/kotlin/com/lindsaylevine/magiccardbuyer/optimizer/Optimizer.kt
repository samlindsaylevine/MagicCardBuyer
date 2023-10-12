package com.lindsaylevine.magiccardbuyer.optimizer

/**
 * Common interface for different strategies of solving a [VendorProblem].
 */
interface Optimizer {
    fun <T> solve(problem: VendorProblem<T>): VendorSolution<T>
}