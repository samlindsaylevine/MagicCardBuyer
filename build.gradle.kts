plugins {
    id("org.jetbrains.kotlin.jvm") version "1.8.0"
    application
}

repositories {
    mavenCentral()
}

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(17)
    }
}

dependencies {
    // Gradle init suggests doing this to make sure that the Kotlin versions are consistent.
    implementation(platform("org.jetbrains.kotlin:kotlin-bom"))
    implementation("org.jetbrains.kotlin:kotlin-stdlib")
    implementation("org.jetbrains.kotlin:kotlin-reflect")

    // Google's OR Tools for solving optimization problems in linear programming.
    implementation("com.google.ortools:ortools-java:9.6.2534")

    // Getting browser cookies to be able to add items to a shopping cart.
    // We've manually stripped the JNA dependency out of this JAR because it is old and conflicts with
    // OR-Tools. This also includes my fix for the Windows bug that can't find the cookies file in the latest
    // version of Chrome.
    implementation(files("lib/CookieMonster-no-jna.jar"))

    // JSON.
    implementation("com.fasterxml.jackson.core:jackson-databind:2.14.2")
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin:2.14.2")

    testImplementation("org.jetbrains.kotlin:kotlin-test")
    testImplementation("org.jetbrains.kotlin:kotlin-test-junit")
    testImplementation("org.assertj:assertj-core:3.14.0")
}

application {
    mainClass.set("com.lindsaylevine.magiccardbuyer.MagicCardBuyerKt")
}
