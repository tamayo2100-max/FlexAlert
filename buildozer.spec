# buildozer.spec - configuracion para compilar FlexAlert a APK
# (la compilacion real del APK se hace en la Fase 5)
# Compilar:  buildozer -v android debug

[app]

# Nombre visible de la app
title = FlexAlert

# Nombre del paquete y dominio (cambialo si quieres)
package.name = flexalert
package.domain = com.tuusuario

# Carpetas/archivos fuente
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json
# Excluir lo que no va en el APK (entorno virtual, exports, etc.)
source.exclude_dirs = venv,export,__pycache__

# Version
version = 0.1

# Dependencias que se empaquetan en el APK
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pyjnius,plyer

# Orientacion
orientation = portrait

# --- Android ---
# Permisos:
#   INTERNET           -> futuras sincronizaciones
#   VIBRATE            -> vibracion de la alarma (Fase 4)
#   POST_NOTIFICATIONS -> mostrar notificaciones (Android 13+)
#   FOREGROUND_SERVICE -> mantener la escucha viva (Fase 4)
# (BIND_NOTIFICATION_LISTENER_SERVICE se agrega en la Fase 4 via manifest)
android.permissions = INTERNET,VIBRATE,POST_NOTIFICATIONS,FOREGROUND_SERVICE

android.api = 34
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a

# Acepta automaticamente las licencias del SDK
android.accept_sdk_license = True

# --- Servicio nativo de escucha de notificaciones (Fase 4/5) ---
# NOTA: el listener nativo (service/FlexNotificationListener.java) se cablea
# en un paso posterior, DESPUES de confirmar que el APK base instala y corre.
# Asi el primer build sale limpio. Para activarlo se descomenta esta linea
# (con la ruta de paquete correcta) + el <service> en el manifest. Ver
# NATIVE_SETUP.md.
# android.add_src = service

[buildozer]
log_level = 2
warn_on_root = 1
