# Guía para grabar el video

Todo lo que necesitas para grabar el Loom sin sorpresas. El guion con los tiempos está en [`video-script.md`](video-script.md).

## 1. Una sola vez (≈10 minutos)

1. Instala las dependencias:
   ```bash
   make install
   ```
2. **(Recomendado) Activa la IA real.** Sin esto la app funciona igual, pero en *modo demostración*: la barra inferior lo indica y el borrador se arma copiando frases de los PDFs, en inglés.
   1. Crea una API key en [console.anthropic.com → API Keys](https://console.anthropic.com/settings/keys). Necesita saldo; un borrador completo cuesta menos de US$1.
   2. Copia la plantilla y pega tu key después de `ANTHROPIC_API_KEY=`, sin comillas ni espacios:
      ```bash
      cp .env.example .env
      ```
      `.env` está en `.gitignore`: nunca se sube a GitHub.
   3. Comprueba que funciona:
      ```bash
      make check-ai
      ```
      Debes ver `✓ Planificador`, `✓ Redactor` y `✓ Verificador`.
3. Abre [excalidraw.com](https://excalidraw.com) y arrastra `board/cip-research-assistant.excalidraw` a la página.

## 2. Justo antes de grabar (≈5 minutos)

1. Levanta todo con un comando (abre la app en el navegador):
   ```bash
   make demo
   ```
2. En la app: **Mi biblioteca** → la ruta de la carpeta de ejemplo ya está escrita → **Abrir**. Espera a ver *7 artículos listos para citar*.
3. **Deja un borrador listo**: *Nuevo borrador* → clic en la primera idea → **Redactar borrador**. Con IA real tarda unos minutos; en modo demostración, segundos. En el video muestras el progreso unos segundos y pasas al borrador ya terminado en *Mis borradores*.
4. Deja dos pestañas, en este orden: **el tablero** y **la app**.
5. Navegador a pantalla completa y zoom al 100 %. Activa *No molestar* para que no salgan notificaciones.

> ¿Quieres usar tus propios PDFs? En *Mi biblioteca* → *Cambiar de carpeta* y escribe la ruta de tu carpeta.

## 3. Momentos de demo en vivo (opcionales, ≈40 s en total)

| Cuándo (ver guion) | Qué hacer en la app |
|---|---|
| ⑥ Revisión | Clic en una afirmación subrayada → muestra el panel → **Ver en el PDF** → cierra → presiona `A` y luego `Ctrl+Z` |
| ⑦ Exportar | **Exportar** → **Exportar** → **Descargar** → abre el `.docx` y muestra un comentario de revisión en Word |

El resto del video se cuenta sobre el tablero.

## 4. Si algo falla

| Síntoma | Solución |
|---|---|
| “No me puedo comunicar con el asistente” | Revisa que `make demo` siga corriendo en la terminal; si no, vuelve a ejecutarlo |
| Error de puerto 8000 o 1420 en uso | Cierra la otra terminal que tenga la app abierta o reinicia la terminal |
| `make check-ai` muestra ✗ por credenciales | Revisa la key en `.env`: una sola línea, sin comillas ni espacios |
| “Hay mucha demanda en el servicio de IA” | Espera uno o dos minutos y reintenta |
| Quiero empezar de cero | `Ctrl+C` en la terminal, borra la carpeta `.data` y vuelve a ejecutar `make demo` |
