plugins {
    id("org.jetbrains.kotlin.jvm") version "1.8.0"
    application
}

repositories {
    mavenCentral()
}

dependencies {
    // Gradle init suggests doing this to make sure that the Kotlin versions are consistent.
    implementation(platform("org.jetbrains.kotlin:kotlin-bom"))
    implementation("org.jetbrains.kotlin:kotlin-stdlib")
    implementation("org.jetbrains.kotlin:kotlin-reflect")

    // Google's OR Tools for solving optimization problems in linear programming.
    implementation("com.google.ortools:ortools-java:9.6.2534")

    // JSON.
    implementation("com.fasterxml.jackson.core:jackson-databind:2.14.2")
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin:2.14.2")

    testImplementation("org.jetbrains.kotlin:kotlin-test")
    testImplementation("org.jetbrains.kotlin:kotlin-test-junit")
    testImplementation("org.assertj:assertj-core:3.14.0")
}

application {
    mainClass.set("com.lindsay-levine.magiccardbuyer.MagicCardBuyer")
}
