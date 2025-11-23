
# Procedimiento Formal: Capacitor a APK de Producción (Release)

## Este procedimiento garantiza la obtención de un archivo ejecutable APK firmado (release) listo para su distribución, utilizando únicamente formato Markdown y terminología formal.

## Requisitos

    Node.js ≥20

    Android Studio descomprimido (ej. ~/android-studio/)

    JDK 17 (incluido en Android Studio)

# Pasos

1. Configuración Inicial del Proyecto y Sincronización

Ejecute los siguientes comandos para inicializar el proyecto Capacitor y configurar el entorno Android:
Bash

Copiar el siguiente index a proyecto_root/src/

```
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>App</title>
</head>
<body>
  <h1>OK</h1>
</body>
</html>
```

```
npx cap init app com.example.app --web-dir src
npm install @capacitor/core @capacitor/cli @capacitor/android
npx cap add android
npx cap sync android
```

2. Apertura del Proyecto en Android Studio

    Abra Android Studio.

    En la pantalla de bienvenida, seleccione Open.

    Navegue y seleccione la carpeta android ubicada dentro del directorio raíz de su proyecto Capacitor. Confirme con OK.

3. Configuración de la Firma (Signing para Release)

La variante release requiere que la aplicación esté firmada mediante un keystore.

    En el menú superior de Android Studio, acceda a: Build → Generate Signed Bundle / APK...

    Seleccione la opción APK.

    Haga clic en Next.

    Verifique que el campo Module muestre app.

    En la sección Key store path:

        Si el archivo de clave (.jks o .keystore) ya existe, selecciónelo.

        Si no, haga clic en Create new... y complete los detalles del Keystore y la Key.

    Proporcione las contraseñas para el Keystore y la Key.

    Haga clic en Next.

4. Generación del APK de Producción (Release)

    En la ventana de Generate Signed Bundle or APK, asegúrese de que en la sección Build Variants esté marcada la opción release.

    Active la casilla Sign the bundle/APK.

    Haga clic en Finish.

El proceso de Gradle se ejecutará para compilar y firmar el archivo binario.

5. Ubicación Final del APK de Producción

Una vez concluida la construcción, el archivo APK de producción, firmado y listo para su distribución, estará disponible en la ruta (relativa al root del proyecto):

android/app/release/app-release.apk
