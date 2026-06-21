# Cableado nativo de la alarma (Fase 4 → Fase 5)

La parte que **escucha las notificaciones de Amazon Flex** necesita un servicio
nativo de Android (`NotificationListenerService`). No se puede probar en la PC;
se termina de cablear al **compilar el APK (Fase 5)**.

## Cómo funciona el puente

```
Amazon Flex manda notificación
        │
        ▼
FlexNotificationListener.java   (servicio nativo, SOLO lee)
        │  escribe el texto en
        ▼
files/flex_notifications.log
        │  la app Kivy lo lee cada 1s (Clock)
        ▼
notification_parser.py → matcher.py → alarm.py
        │
        ▼   si cumple tus filtros:
🚨 ALARMA + vibración + "último bloque" en pantalla
```

## Qué falta para la Fase 5

1. **Manifest** — declarar el servicio con el permiso del sistema:

```xml
<service
    android:name="com.tuusuario.flexalert.FlexNotificationListener"
    android:label="FlexAlert Listener"
    android:permission="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE"
    android:exported="false">
    <intent-filter>
        <action android:name="android.service.notification.NotificationListenerService" />
    </intent-filter>
</service>
```

2. **buildozer.spec** — incluir el `.java`:
   - `android.add_src = service`  (carpeta con el .java en su ruta de paquete)
   - añadir el bloque `<service>` de arriba vía `android.extra_manifest_xml`
     o un template de manifest.

3. **Permiso del usuario** (una sola vez, en el teléfono):
   Ajustes → Notificaciones → Acceso a notificaciones → activar **FlexAlert**.
   (Android obliga a que el usuario lo active a mano; ninguna app puede
   auto-otorgárselo. Es la garantía de privacidad del sistema.)

## Importante / honesto

- Este servicio **solo lee** notificaciones. No refresca, no toca, no acepta
  bloques. Eso lo haces tú. Por eso no viola los términos de Amazon como sí
  lo hace el auto-tap.
- En la PC, el botón **"Probar con bloque de ejemplo"** ejecuta TODO el
  pipeline (parser → filtros → alarma) con un texto de muestra, para validar
  la lógica sin necesidad del teléfono.
