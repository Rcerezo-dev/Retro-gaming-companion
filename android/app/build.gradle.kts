import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

// App Key de Dropbox (ANDROID-SYNC-5) — nunca hardcodeada ni versionada.
// Se lee de android/local.properties (ignorado por git), clave
// "dropbox.appKey". Sin ella, la app compila igual (OAuth deshabilitado en
// runtime) — ver DropboxAuthManager.isAppKeyConfigured() y
// android/local.properties.example.
val localProperties =
    Properties().apply {
        val localPropertiesFile = rootProject.file("local.properties")
        if (localPropertiesFile.exists()) {
            localPropertiesFile.inputStream().use { load(it) }
        }
    }
val dropboxAppKey: String = localProperties.getProperty("dropbox.appKey", "")

android {
    namespace = "com.retrovault.android"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.retrovault.android"
        // minSdk 26 (Android 8.0): cubre las handhelds retro Android modernas
        // (RG556, RG35XX H, Odin2, Retroid Pocket...) sin cargar con ramas de
        // compatibilidad para versiones realmente antiguas. Ver
        // Tareas/Roadmap-Android-Sync.md §3 para el modelo de permisos por
        // rango de API (26-29 legacy storage, 30+ MANAGE_EXTERNAL_STORAGE,
        // 33+ POST_NOTIFICATIONS, 34+ FOREGROUND_SERVICE_DATA_SYNC).
        minSdk = 26
        targetSdk = 34
        versionCode = 1
        versionName = "0.1.0"

        buildConfigField("String", "DROPBOX_APP_KEY", "\"$dropboxAppKey\"")
        // AuthActivity del SDK de Dropbox necesita el scheme "db-<APP_KEY>"
        // declarado en el manifest — ver AndroidManifest.xml.
        manifestPlaceholders["dropboxAppKey"] = dropboxAppKey
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    composeOptions {
        // Debe emparejar con la versión de Kotlin del plugin raíz (1.9.24) —
        // ver el mapa de compatibilidad Compose↔Kotlin de Google antes de
        // subir cualquiera de las dos versiones.
        kotlinCompilerExtensionVersion = "1.5.14"
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.4")
    implementation("androidx.activity:activity-compose:1.9.1")
    implementation(platform("androidx.compose:compose-bom:2024.06.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")

    // ANDROID-SYNC-5/6: OAuth PKCE de Dropbox + storage cifrado de la
    // credencial. dropbox-android-sdk trae Auth/AuthActivity (helper de
    // Android); dropbox-core-sdk trae DbxClientV2 y el resto del API v2
    // (ambos en Maven Central desde 7.0.0, ya no dependen de JCenter).
    implementation("com.dropbox.core:dropbox-core-sdk:7.0.0")
    implementation("com.dropbox.core:dropbox-android-sdk:7.0.0")
    implementation("androidx.security:security-crypto:1.1.0")

    // Dependencias de fases futuras (Room, WorkManager, datastore-preferences)
    // se añaden en sus propios PRs — ANDROID-SYNC-7/8/12 — para mantener
    // cada fase enfocada. No adelantarlas aquí sin código que las use.

    testImplementation("junit:junit:4.13.2")

    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.6.1")
    androidTestImplementation(platform("androidx.compose:compose-bom:2024.06.00"))
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")

    debugImplementation("androidx.compose.ui:ui-tooling")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
