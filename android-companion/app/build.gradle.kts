plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

val releaseKeystorePath = System.getenv("GHOST_KEYSTORE_FILE")
val releaseStorePassword = System.getenv("GHOST_KEYSTORE_PASSWORD")
val releaseKeyAlias = System.getenv("GHOST_KEY_ALIAS")
val releaseKeyPassword = System.getenv("GHOST_KEY_PASSWORD")

android {
    namespace = "com.ghost.securitycenter"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.ghost.securitycenter"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0"
    }

    signingConfigs {
        create("release") {
            storeFile = file(
                releaseKeystorePath ?: "MISSING_GHOST_RELEASE_KEYSTORE"
            )
            storePassword = releaseStorePassword.orEmpty()
            keyAlias = releaseKeyAlias.orEmpty()
            keyPassword = releaseKeyPassword.orEmpty()
        }
    }

    buildTypes {
        getByName("release") {
            signingConfig = signingConfigs.getByName("release")
        }
    }

    buildFeatures {
        compose = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

kotlin {
    compilerOptions {
        jvmTarget.set(
            org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
        )
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2025.10.00")

    implementation(composeBom)
    androidTestImplementation(composeBom)

    implementation("androidx.activity:activity-compose:1.10.1")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")

    debugImplementation("androidx.compose.ui:ui-tooling")
}
