package com.lindsaylevine.magiccardbuyer

import org.assertj.core.api.Assertions.assertThat
import kotlin.test.Test

class MagicCardBuyerTest {
    @Test
    fun testAppHasAGreeting() {
        val classUnderTest = App()

        assertThat(classUnderTest.greeting).isNotNull()
    }
}
