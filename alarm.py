"""
alarm.py  -  Dispara la alarma: sonido fuerte + vibracion.

En el TELEFONO (Android): usa el tono de alarma del sistema + vibracion
mediante pyjnius. En la PC: usa un beep de respaldo para probar el flujo.

Devuelve el "modo" usado: "android" o "desktop".
"""


def trigger_alarm() -> str:
    # ---- Intento en Android (pyjnius) ----
    try:
        from jnius import autoclass  # solo existe en el telefono

        # Vibracion
        try:
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Context = autoclass("android.content.Context")
            activity = PythonActivity.mActivity
            vibrator = activity.getSystemService(Context.VIBRATOR_SERVICE)
            VibrationEffect = autoclass("android.os.VibrationEffect")
            # patron: espera, vibra, pausa, vibra...
            pattern = [0, 600, 200, 600, 200, 600]
            effect = VibrationEffect.createWaveform(pattern, -1)
            vibrator.vibrate(effect)
        except Exception:
            pass

        # Sonido de alarma del sistema (suena aunque este en silencio segun config)
        try:
            RingtoneManager = autoclass("android.media.RingtoneManager")
            uri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            ringtone = RingtoneManager.getRingtone(
                PythonActivity.mActivity.getApplicationContext(), uri
            )
            ringtone.play()
        except Exception:
            pass

        return "android"

    except Exception:
        # ---- Respaldo en PC (para probar el flujo) ----
        try:
            import winsound
            for _ in range(3):
                winsound.Beep(1000, 400)
        except Exception:
            print("\a")  # campana del terminal
        return "desktop"
