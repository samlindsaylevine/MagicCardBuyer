plugins {
    id("org.jetbrains.kotlin.jvm") version "1.3.41"
    application
}

repositories {
    jcenter()
    mavenCentral()
}

dependencies {
    // Gradle init suggests doing this to make sure that the Kotlin versions are consistent.
    implementation(platform("org.jetbrains.kotlin:kotlin-bom"))
    implementation("org.jetbrains.kotlin:kotlin-stdlib-jdk8")

    // Google's OR Tools for solving optimization problems in linear programming.
    implementation("com.google.ortools:ortools-java:9.6.2534")

    testImplementation("org.jetbrains.kotlin:kotlin-test")
    testImplementation("org.jetbrains.kotlin:kotlin-test-junit")
    testImplementation("org.assertj:assertj-core:3.14.0")
}

application {
    mainClassName = "com.lindsay-levine.magiccardbuyer.MagicCardBuyer"
}
