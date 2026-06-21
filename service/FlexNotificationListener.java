/*
 * FlexNotificationListener.java
 * ------------------------------
 * Servicio nativo de Android que ESCUCHA las notificaciones del sistema.
 * Cuando llega una notificacion de la app de Amazon Flex, escribe su texto
 * en un archivo (flex_notifications.log) que la app Python (Kivy) lee y
 * procesa con el parser + los filtros + la alarma.
 *
 * IMPORTANTE: este servicio SOLO LEE notificaciones que Amazon ya mando.
 * No toca la app de Amazon, no refresca, no acepta nada. Tu decides.
 *
 * Se conecta en la Fase 5 (compilacion) via buildozer. Ver NATIVE_SETUP.md.
 */
package com.tuusuario.flexalert;

import android.app.Notification;
import android.os.Bundle;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;

import java.io.File;
import java.io.FileWriter;

public class FlexNotificationListener extends NotificationListenerService {

    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        try {
            String pkg = sbn.getPackageName();
            if (pkg == null) return;

            // Solo notificaciones de la app de Amazon Flex
            String p = pkg.toLowerCase();
            boolean isFlex = (p.contains("amazon") && p.contains("rabbit"))
                          || p.contains("flex");
            if (!isFlex) return;

            Notification n = sbn.getNotification();
            if (n == null || n.extras == null) return;
            Bundle ex = n.extras;

            CharSequence title = ex.getCharSequence(Notification.EXTRA_TITLE);
            CharSequence text  = ex.getCharSequence(Notification.EXTRA_TEXT);
            CharSequence big   = ex.getCharSequence(Notification.EXTRA_BIG_TEXT);

            StringBuilder sb = new StringBuilder();
            if (title != null) sb.append(title).append(" ");
            if (text  != null) sb.append(text).append(" ");
            if (big   != null) sb.append(big);

            String line = System.currentTimeMillis() + "\t"
                        + sb.toString().replace("\n", " ").trim() + "\n";

            File f = new File(getFilesDir(), "flex_notifications.log");
            FileWriter w = new FileWriter(f, true);
            w.write(line);
            w.close();
        } catch (Exception e) {
            // nunca crashear por una notificacion
        }
    }

    @Override
    public void onNotificationRemoved(StatusBarNotification sbn) {
        // no nos interesa
    }
}
