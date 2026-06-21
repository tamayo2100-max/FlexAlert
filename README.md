# FlexAlert 🔔

App **propia y legítima** de alertas para conductores de Amazon Flex.
Construida 100% en Python con **Kivy + KivyMD**.

> **Filosofía:** la app te **avisa** al instante cuando aparece un buen bloque —
> **tú** decides y aceptas. Sin auto-tap, sin auto-refresh. Así no arriesgas
> tu cuenta de Amazon (esos automatismos violan sus términos y son la causa #1
> de desactivación de conductores).

---

## ✨ Funciones (tomadas de lo mejor del rubro)

| Pestaña | Qué hace |
|---------|----------|
| 🔔 **Alerta** | Alarma fuerte cuando aparece un bloque que cumple tus filtros |
| 🎯 **Filtros** | Pago mínimo ($/hora), estación, horario y duración |
| 📊 **Dashboard** | Tu $/hora real, bloques del mes, mejores estaciones |
| 📝 **Log** | Historial de bloques + exportar CSV para impuestos |

---

## 🗺️ Plan por fases

- [x] **Fase 1** — Esqueleto + UI base (4 pantallas con navegación)
- [x] **Fase 2** — Filtros funcionales + guardado en SQLite + presets
- [x] **Fase 3** — Block Log + Dashboard + Export CSV
- [x] **Fase 4** — Parser + filtros + alarma + servicio nativo ← *estás aquí*
- [ ] **Fase 5** — Compilar el APK con Buildozer

> **Fase 4 — detalle:** el cerebro (parser → filtros → alarma) está hecho y
> probado en PC. El servicio nativo que escucha las notificaciones de Flex
> (`service/FlexNotificationListener.java`) se termina de cablear al compilar.
> Ver [NATIVE_SETUP.md](NATIVE_SETUP.md).

---

## ▶️ Probar en la PC

```bash
pip install -r requirements.txt
python main.py
```

Se abre una ventana del tamaño de un teléfono para que veas el diseño.
Prueba el switch de la alarma y el botón de tema claro/oscuro (arriba a la derecha).

---

## 📱 Compilar el APK (Fase 5)

La compilación se hace con **Buildozer** (requiere Linux o WSL en Windows):

```bash
buildozer -v android debug
```

El `buildozer.spec` ya está preconfigurado con permisos y dependencias.
