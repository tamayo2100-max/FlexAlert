"""
FlexAlert  -  App de alertas legitima para conductores de Amazon Flex.
====================================================================

FASE 1: esqueleto + UI base (4 pantallas con navegacion inferior).  [HECHO]
FASE 2: filtros funcionales + guardado en SQLite + presets.          [HECHO]

Construida 100% en Python con Kivy + KivyMD.

Inspirada en las MEJORES funciones LEGITIMAS de la app premium analizada:
  - Alarma de bloques (Block Alert)          -> pestana "Alerta"
  - Filtros (pago $/h, estacion, horario)    -> pestana "Filtros"
  - Dashboard de ganancias ($/hora real)     -> pestana "Dashboard"
  - Block Log + Export CSV                    -> pestana "Log"

NO incluye auto-tap / auto-refresh: eso viola los terminos de Amazon Flex
y arriesga la desactivacion de la cuenta. Esta app AVISA, tu decides.

Probar en PC:   venv\\Scripts\\python.exe main.py
"""

from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.core.window import Window
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import (
    OneLineAvatarIconListItem, TwoLineAvatarIconListItem,
    IconLeftWidget, IconRightWidget,
)
from kivymd.uix.pickers import MDTimePicker
from kivymd.toast import toast

import os
from datetime import datetime

import db
import notification_parser
import matcher
import alarm

# Solo para probar en el PC: simula el tamano de un telefono.
Window.size = (380, 760)


KV = '''
MDScreen:

    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "FlexAlert"
            elevation: 3
            left_action_items: [["lightning-bolt", lambda x: None]]
            right_action_items: [["theme-light-dark", lambda x: app.toggle_theme()]]

        MDBottomNavigation:
            panel_color: app.theme_cls.bg_darkest
            selected_color_background: app.theme_cls.primary_color
            text_color_active: app.theme_cls.primary_color

            # ----------------------------------------------------------
            # PESTANA 1: ALERTA
            # ----------------------------------------------------------
            MDBottomNavigationItem:
                name: "alerta"
                text: "Alerta"
                icon: "bell-ring"

                MDBoxLayout:
                    orientation: "vertical"
                    padding: "16dp"
                    spacing: "16dp"

                    MDCard:
                        orientation: "vertical"
                        padding: "20dp"
                        spacing: "10dp"
                        size_hint_y: None
                        height: "200dp"
                        radius: [20, 20, 20, 20]
                        md_bg_color: app.theme_cls.primary_color

                        MDLabel:
                            text: "Estado de la alarma"
                            font_style: "Caption"
                            theme_text_color: "Custom"
                            text_color: 1, 1, 1, 0.8

                        MDLabel:
                            id: alarm_state_label
                            text: "DESACTIVADA"
                            font_style: "H4"
                            bold: True
                            theme_text_color: "Custom"
                            text_color: 1, 1, 1, 1

                        MDBoxLayout:
                            adaptive_height: True
                            spacing: "8dp"

                            MDLabel:
                                text: "Avisame cuando aparezca un buen bloque"
                                font_style: "Body2"
                                theme_text_color: "Custom"
                                text_color: 1, 1, 1, 0.9

                            MDSwitch:
                                id: alarm_switch
                                pos_hint: {"center_y": 0.5}
                                on_active: app.toggle_alarm(self.active)

                    MDLabel:
                        text: "Ultimo bloque detectado"
                        font_style: "Subtitle1"
                        bold: True
                        adaptive_height: True

                    MDCard:
                        orientation: "vertical"
                        padding: "20dp"
                        size_hint_y: None
                        height: "120dp"
                        radius: [16, 16, 16, 16]

                        MDLabel:
                            id: last_block_label
                            text: "Aun no hay bloques.\\nActiva la alarma y deja la app corriendo."
                            font_style: "Body2"
                            theme_text_color: "Hint"
                            halign: "center"

                    MDRaisedButton:
                        text: "Probar con bloque de ejemplo"
                        size_hint_x: 1
                        on_release: app.test_pipeline()

                    Widget:

            # ----------------------------------------------------------
            # PESTANA 2: FILTROS
            # ----------------------------------------------------------
            MDBottomNavigationItem:
                name: "filtros"
                text: "Filtros"
                icon: "filter-variant"

                MDBoxLayout:
                    orientation: "vertical"
                    padding: "16dp"
                    spacing: "12dp"

                    MDLabel:
                        text: "Solo me suena lo que vale la pena"
                        font_style: "Subtitle1"
                        bold: True
                        adaptive_height: True

                    FilterRow:
                        id: row_pay
                        key: "pay"
                        icon: "cash"
                        title: "Pago minimo ($/hora)"
                        value: "Sin configurar"

                    FilterRow:
                        id: row_stations
                        key: "stations"
                        icon: "map-marker"
                        title: "Estaciones"
                        value: "Todas"

                    FilterRow:
                        id: row_time
                        key: "time"
                        icon: "clock-outline"
                        title: "Horario de inicio"
                        value: "Cualquiera"

                    FilterRow:
                        id: row_dur
                        key: "dur"
                        icon: "timer-sand"
                        title: "Duracion del bloque"
                        value: "Cualquiera"

                    Widget:

                    MDBoxLayout:
                        adaptive_height: True
                        spacing: "10dp"
                        size_hint_y: None
                        height: "48dp"

                        MDRaisedButton:
                            text: "Guardar preset"
                            on_release: app.dialog_save_preset()

                        MDFlatButton:
                            text: "Cargar preset"
                            on_release: app.dialog_load_preset()

            # ----------------------------------------------------------
            # PESTANA 3: DASHBOARD
            # ----------------------------------------------------------
            MDBottomNavigationItem:
                name: "dashboard"
                text: "Dashboard"
                icon: "chart-line"

                MDBoxLayout:
                    orientation: "vertical"
                    padding: "16dp"
                    spacing: "12dp"

                    MDLabel:
                        text: "Tus numeros reales"
                        font_style: "Subtitle1"
                        bold: True
                        adaptive_height: True

                    MDBoxLayout:
                        spacing: "12dp"
                        size_hint_y: None
                        height: "110dp"

                        StatCard:
                            id: stat_payhour
                            value: "$0.0"
                            label: "$/hora promedio"

                        StatCard:
                            id: stat_count
                            value: "0"
                            label: "Bloques este mes"

                    MDBoxLayout:
                        spacing: "12dp"
                        size_hint_y: None
                        height: "110dp"

                        StatCard:
                            id: stat_total
                            value: "$0"
                            label: "Ganancia total"

                        StatCard:
                            id: stat_best
                            value: "-"
                            label: "Mejor estacion"

                    Widget:

            # ----------------------------------------------------------
            # PESTANA 4: BLOCK LOG
            # ----------------------------------------------------------
            MDBottomNavigationItem:
                name: "log"
                text: "Log"
                icon: "format-list-bulleted"

                MDBoxLayout:
                    orientation: "vertical"
                    padding: "16dp"
                    spacing: "12dp"

                    MDBoxLayout:
                        adaptive_height: True

                        MDLabel:
                            text: "Historial de bloques"
                            font_style: "Subtitle1"
                            bold: True

                        MDIconButton:
                            icon: "file-export"
                            on_release: app.export_csv()

                    MDRaisedButton:
                        text: "+ Agregar bloque"
                        size_hint_x: 1
                        on_release: app.dialog_add_block()

                    MDScrollView:
                        MDList:
                            id: log_list


# Fila reutilizable y clickable para la pantalla de Filtros
<FilterRow@MDCard>:
    icon: "cog"
    title: ""
    value: ""
    key: ""
    orientation: "horizontal"
    padding: "14dp"
    spacing: "14dp"
    size_hint_y: None
    height: "72dp"
    radius: [14, 14, 14, 14]
    ripple_behavior: True
    focus_behavior: True
    on_release: app.on_filter_tap(root.key)

    MDIcon:
        icon: root.icon
        theme_text_color: "Custom"
        text_color: app.theme_cls.primary_color
        size_hint_x: None
        width: "32dp"
        pos_hint: {"center_y": 0.5}

    MDBoxLayout:
        orientation: "vertical"
        pos_hint: {"center_y": 0.5}

        MDLabel:
            text: root.title
            font_style: "Body1"
            bold: True
            adaptive_height: True

        MDLabel:
            text: root.value
            font_style: "Caption"
            theme_text_color: "Hint"
            adaptive_height: True

    MDIcon:
        icon: "chevron-right"
        theme_text_color: "Hint"
        size_hint_x: None
        width: "24dp"
        pos_hint: {"center_y": 0.5}


# Tarjeta de estadistica para el Dashboard
<StatCard@MDCard>:
    value: ""
    label: ""
    orientation: "vertical"
    padding: "16dp"
    radius: [16, 16, 16, 16]

    MDLabel:
        text: root.value
        font_style: "H5"
        bold: True
        theme_text_color: "Custom"
        text_color: app.theme_cls.primary_color
        adaptive_height: True

    MDLabel:
        text: root.label
        font_style: "Caption"
        theme_text_color: "Hint"
'''


class FlexAlertApp(MDApp):

    dialog = None  # dialogo activo (reutilizado)

    def build(self):
        self.title = "FlexAlert"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"
        db.init_db()
        return Builder.load_string(KV)

    def on_start(self):
        # Carga lo guardado y lo muestra en pantalla
        def _load(dt):
            self.refresh_filters_display()
            self.refresh_dashboard()
            self.refresh_log()
        Clock.schedule_once(_load, 0.1)

    # ==========================================================
    #  ALERTA
    # ==========================================================
    def toggle_theme(self):
        self.theme_cls.theme_style = (
            "Light" if self.theme_cls.theme_style == "Dark" else "Dark"
        )

    listening = False
    _poll_event = None
    _notif_pos = 0  # cuanto del archivo de notificaciones ya leimos

    def toggle_alarm(self, active: bool):
        self.root.ids.alarm_state_label.text = (
            "ACTIVADA" if active else "DESACTIVADA"
        )
        self.listening = active
        if active:
            # Empieza a sondear el archivo que escribe el servicio nativo (Android).
            # En PC no hay archivo: el sondeo no hace nada hasta que pruebes manual.
            if self._poll_event is None:
                self._poll_event = Clock.schedule_interval(self._poll_notifications, 1.0)
        else:
            if self._poll_event is not None:
                self._poll_event.cancel()
                self._poll_event = None

    def _notif_log_path(self):
        """Ruta del archivo donde el servicio nativo deja las notificaciones."""
        try:
            from jnius import autoclass  # Android
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            files_dir = PythonActivity.mActivity.getFilesDir().getAbsolutePath()
            return os.path.join(files_dir, "flex_notifications.log")
        except Exception:
            # En PC: archivo local (solo para pruebas manuales)
            return os.path.join(os.path.dirname(__file__), "flex_notifications.log")

    def _poll_notifications(self, dt):
        """Lee lineas nuevas del log y procesa cada notificacion."""
        path = self._notif_log_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as fh:
                fh.seek(self._notif_pos)
                new = fh.read()
                self._notif_pos = fh.tell()
        except Exception:
            return
        for line in new.splitlines():
            if not line.strip():
                continue
            text = line.split("\t", 1)[-1]  # quitar timestamp si lo trae
            self.process_notification(text)

    def process_notification(self, text: str) -> bool:
        """Pipeline: parsear -> filtrar -> (si cumple) alarma + mostrar."""
        block = notification_parser.parse_notification(text)
        if not block:
            return False
        ok, reason = matcher.match_block(block, db.get_filters())
        if ok:
            alarm.trigger_alarm()
            self._show_block(block, matched=True)
            toast("BLOQUE BUENO! Abre Flex y acepta")
            return True
        else:
            self._show_block(block, matched=False, reason=reason)
            return False

    def _show_block(self, block, matched, reason=""):
        st = block.get("station") or "Estacion ?"
        pay = block.get("pay")
        dur = block.get("duration")
        ph = block.get("pay_hour")
        parts = [st]
        if pay:
            parts.append(f"${pay:.0f}")
        if dur:
            parts.append(f"{dur:g}h")
        if ph:
            parts.append(f"${ph:.1f}/h")
        line = "  -  ".join(parts)
        if matched:
            self.root.ids.last_block_label.text = f"[CUMPLE]\n{line}"
        else:
            self.root.ids.last_block_label.text = f"(descartado)\n{line}\n{reason}"

    def test_pipeline(self):
        """Corre el pipeline completo con un bloque de ejemplo (prueba en PC)."""
        sample = "Offer available $66.00 - 3 hr 0 min - DLA5 - Starts 6:00 AM"
        matched = self.process_notification(sample)
        if matched:
            toast("Ejemplo CUMPLE tus filtros -> alarma disparada")
        else:
            toast("Ejemplo descartado por tus filtros (mira la tarjeta)")

    # ==========================================================
    #  FILTROS  -  mostrar valores guardados
    # ==========================================================
    def refresh_filters_display(self):
        cfg = db.get_filters()
        ids = self.root.ids

        # Pago
        pay = cfg["min_pay_hour"]
        ids.row_pay.value = f"$ {pay:.0f}/hora o mas" if pay > 0 else "Sin configurar"

        # Estaciones
        st = cfg["stations"]
        ids.row_stations.value = ", ".join(st) if st else "Todas"

        # Horario
        ts, te = cfg["time_start"], cfg["time_end"]
        ids.row_time.value = f"{ts} - {te}" if ts and te else "Cualquiera"

        # Duracion
        dmin, dmax = cfg["dur_min"], cfg["dur_max"]
        if dmin or dmax:
            ids.row_dur.value = f"{dmin:g}h - {dmax:g}h"
        else:
            ids.row_dur.value = "Cualquiera"

    def on_filter_tap(self, key: str):
        if key == "pay":
            self.dialog_pay()
        elif key == "stations":
            self.dialog_stations()
        elif key == "time":
            self.dialog_time()
        elif key == "dur":
            self.dialog_duration()

    def _close_dialog(self, *_):
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None

    # ----- Dialogo: Pago minimo -----
    def dialog_pay(self):
        cfg = db.get_filters()
        field = MDTextField(
            hint_text="Pago minimo por hora (ej. 20)",
            input_filter="float",
            text=str(cfg["min_pay_hour"] or ""),
        )
        content = MDBoxLayout(
            field, orientation="vertical", spacing="12dp",
            size_hint_y=None, height="80dp",
        )

        def save(*_):
            try:
                val = float(field.text or 0)
            except ValueError:
                val = 0.0
            db.set_filter("min_pay_hour", val)
            self.refresh_filters_display()
            toast("Pago minimo guardado")
            self._close_dialog()

        self.dialog = MDDialog(
            title="Pago minimo ($/hora)",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Cancelar", on_release=self._close_dialog),
                MDRaisedButton(text="Guardar", on_release=save),
            ],
        )
        self.dialog.open()

    # ----- Dialogo: Estaciones -----
    def dialog_stations(self):
        cfg = db.get_filters()
        field = MDTextField(
            hint_text="Estaciones separadas por coma (ej. DLA5, DAX8)",
            text=", ".join(cfg["stations"]),
        )
        content = MDBoxLayout(
            field, orientation="vertical", spacing="12dp",
            size_hint_y=None, height="80dp",
        )

        def save(*_):
            stations = [s.strip().upper() for s in field.text.split(",") if s.strip()]
            db.set_filter("stations", stations)
            self.refresh_filters_display()
            toast("Estaciones guardadas")
            self._close_dialog()

        self.dialog = MDDialog(
            title="Estaciones (vacio = todas)",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Cancelar", on_release=self._close_dialog),
                MDRaisedButton(text="Guardar", on_release=save),
            ],
        )
        self.dialog.open()

    # ----- Dialogo: Horario (dos time pickers encadenados) -----
    def dialog_time(self):
        def pick_end(_inst, start_time):
            start_str = start_time.strftime("%H:%M")

            def save_end(_i2, end_time):
                db.set_filter("time_start", start_str)
                db.set_filter("time_end", end_time.strftime("%H:%M"))
                self.refresh_filters_display()
                toast("Horario guardado")

            end_picker = MDTimePicker()
            end_picker.bind(on_save=save_end)
            end_picker.open()
            toast("Ahora elige la hora FINAL")

        start_picker = MDTimePicker()
        start_picker.bind(on_save=pick_end)
        start_picker.open()
        toast("Elige la hora de INICIO mas temprana")

    # ----- Dialogo: Duracion (min y max) -----
    def dialog_duration(self):
        cfg = db.get_filters()
        f_min = MDTextField(
            hint_text="Duracion minima (horas, ej. 2)",
            input_filter="float", text=str(cfg["dur_min"] or ""),
        )
        f_max = MDTextField(
            hint_text="Duracion maxima (horas, ej. 5)",
            input_filter="float", text=str(cfg["dur_max"] or ""),
        )
        content = MDBoxLayout(
            f_min, f_max, orientation="vertical", spacing="12dp",
            size_hint_y=None, height="150dp",
        )

        def save(*_):
            try:
                dmin = float(f_min.text or 0)
                dmax = float(f_max.text or 0)
            except ValueError:
                dmin = dmax = 0.0
            db.set_filter("dur_min", dmin)
            db.set_filter("dur_max", dmax)
            self.refresh_filters_display()
            toast("Duracion guardada")
            self._close_dialog()

        self.dialog = MDDialog(
            title="Duracion del bloque (horas)",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Cancelar", on_release=self._close_dialog),
                MDRaisedButton(text="Guardar", on_release=save),
            ],
        )
        self.dialog.open()

    # ==========================================================
    #  PRESETS
    # ==========================================================
    def dialog_save_preset(self):
        field = MDTextField(hint_text="Nombre del preset (ej. Mananas buenas)")
        content = MDBoxLayout(
            field, orientation="vertical", spacing="12dp",
            size_hint_y=None, height="80dp",
        )

        def save(*_):
            name = field.text.strip()
            if not name:
                toast("Ponle un nombre al preset")
                return
            db.save_preset(name, db.get_filters())
            toast(f"Preset '{name}' guardado")
            self._close_dialog()

        self.dialog = MDDialog(
            title="Guardar preset",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Cancelar", on_release=self._close_dialog),
                MDRaisedButton(text="Guardar", on_release=save),
            ],
        )
        self.dialog.open()

    def dialog_load_preset(self):
        presets = db.list_presets()
        if not presets:
            toast("No tienes presets guardados todavia")
            return

        items = []
        for pid, name, config in presets:
            item = OneLineAvatarIconListItem(text=name)
            item.add_widget(IconLeftWidget(icon="bookmark"))

            def make_apply(cfg=config):
                def _apply(*_):
                    db.set_filters(cfg)
                    self.refresh_filters_display()
                    toast("Preset aplicado")
                    self._close_dialog()
                return _apply
            item.on_release = make_apply()

            del_btn = IconRightWidget(icon="trash-can-outline")

            def make_del(the_id=pid):
                def _del(*_):
                    db.delete_preset(the_id)
                    self._close_dialog()
                    toast("Preset eliminado")
                return _del
            del_btn.on_release = make_del()
            item.add_widget(del_btn)
            items.append(item)

        self.dialog = MDDialog(
            title="Cargar preset",
            type="confirmation",
            items=items,
            buttons=[MDFlatButton(text="Cerrar", on_release=self._close_dialog)],
        )
        self.dialog.open()

    # ==========================================================
    #  DASHBOARD
    # ==========================================================
    def refresh_dashboard(self):
        s = db.dashboard_stats()
        ids = self.root.ids
        ids.stat_payhour.value = f"${s['avg_pay_hour']:.1f}"
        ids.stat_count.value = str(s["count_month"])
        ids.stat_total.value = f"${s['total_earnings']:.0f}"
        ids.stat_best.value = s["best_station"]

    # ==========================================================
    #  BLOCK LOG
    # ==========================================================
    def refresh_log(self):
        log_list = self.root.ids.log_list
        log_list.clear_widgets()
        blocks = db.list_blocks()

        if not blocks:
            item = OneLineAvatarIconListItem(text="Sin bloques. Toca '+ Agregar bloque'")
            item.add_widget(IconLeftWidget(icon="information-outline"))
            log_list.add_widget(item)
            return

        for b in blocks:
            item = TwoLineAvatarIconListItem(
                text=f"{b['station'] or 'Estacion ?'}  -  {b['date']}",
                secondary_text=(
                    f"${b['pay']:.0f}  -  {b['duration']:g}h  -  "
                    f"${b['pay_hour']:.1f}/h"
                ),
            )
            item.add_widget(IconLeftWidget(icon="package-variant-closed"))
            right = IconRightWidget(icon="trash-can-outline")

            def make_del(the_id=b["id"]):
                def _del(*_):
                    db.delete_block(the_id)
                    self.refresh_log()
                    self.refresh_dashboard()
                    toast("Bloque eliminado")
                return _del
            right.bind(on_release=make_del())
            item.add_widget(right)
            log_list.add_widget(item)

    def dialog_add_block(self):
        today = datetime.now().strftime("%Y-%m-%d")
        f_date = MDTextField(hint_text="Fecha (AAAA-MM-DD)", text=today)
        f_station = MDTextField(hint_text="Estacion (ej. DLA5)")
        f_pay = MDTextField(hint_text="Pago total ($)", input_filter="float")
        f_dur = MDTextField(hint_text="Duracion (horas, ej. 3.5)", input_filter="float")
        content = MDBoxLayout(
            f_date, f_station, f_pay, f_dur,
            orientation="vertical", spacing="10dp",
            size_hint_y=None, height="270dp",
        )

        def save(*_):
            try:
                pay = float(f_pay.text or 0)
                dur = float(f_dur.text or 0)
            except ValueError:
                toast("Pago y duracion deben ser numeros")
                return
            if pay <= 0 or dur <= 0:
                toast("Pon pago y duracion validos")
                return
            db.add_block(
                f_date.text.strip() or today,
                f_station.text.strip().upper(),
                pay, dur,
            )
            self.refresh_log()
            self.refresh_dashboard()
            toast("Bloque agregado")
            self._close_dialog()

        self.dialog = MDDialog(
            title="Agregar bloque",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Cancelar", on_release=self._close_dialog),
                MDRaisedButton(text="Guardar", on_release=save),
            ],
        )
        self.dialog.open()

    def export_csv(self):
        blocks = db.list_blocks()
        if not blocks:
            toast("No hay bloques para exportar")
            return
        out_dir = os.path.join(os.path.dirname(__file__), "export")
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(
            out_dir, f"flexalert_bloques_{datetime.now():%Y%m%d_%H%M%S}.csv"
        )
        n = db.export_blocks_csv(path)
        toast(f"Exportados {n} bloques a export/")
        print(f"[FlexAlert] CSV: {path}")


if __name__ == "__main__":
    FlexAlertApp().run()
