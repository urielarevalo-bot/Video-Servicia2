# Servicia — Video promocional para Meta Ads (campaña de tráfico)

Video animado generado programáticamente con el estilo de referencia (fondo oscuro,
orbes de cristal translúcidos con neón y glow) y la identidad visual de
[servicia.com.mx](https://servicia.com.mx/) (paleta crema/cobre/verde salvia,
tipografías Archivo e Inter).

## Archivos

| Archivo | Descripción |
|---|---|
| `servicia_meta_ad_9x16.mp4` | Video final — 1080×1920 (9:16), 15 s, 30 fps, H.264 (~4.3 MB) |
| `render_video.py` | Script generador (Python + Pillow + NumPy, codifica con ffmpeg) |
| `previews/` | 6 frames clave — úsalos como thumbnail del anuncio |

## Guion (15 s)

| Tiempo | Escena |
|---|---|
| 0–2.8 s | Hook: "Toda empresa opera en dos frentes. Cubrimos los dos." |
| 2.8–6 s | Frente 01 · En el piso — operación de personal (limpieza, eventos, hotelería, logística) |
| 6–9.2 s | Frente 02 · En la oficina — administración operada (facturación, cobranza, pagos, atención) |
| 9.2–12.2 s | Modelo: Inteligencia + Gente + Supervisión · 90 días · 24/7 · 100% REPSE e IMSS |
| 12.2–15 s | CTA: "Agenda tu diagnóstico operativo" → servicia.com.mx |

## Regenerar el video

```bash
pip install pillow numpy imageio-ffmpeg
# fuentes: Archivo e Inter (Google Fonts) en /tmp:
#   /tmp/Archivo[wdth,wght].ttf y /tmp/Inter[opsz,wght].ttf
python3 render_video.py            # render completo → servicia_meta_ad_9x16.mp4
python3 render_video.py 105        # preview de un solo frame (número de frame)
```

## Especificaciones para Meta Ads (objetivo: Tráfico)

- **Formato:** 9:16 vertical — colócalo en Reels y Stories; también aceptado en Feed y in-stream.
- **Resolución mínima recomendada por Meta:** 1080×1920 ✓ · códec H.264, `yuv420p`, `+faststart` ✓
- **Duración:** 15 s (dentro del rango ideal de 5–15 s para tráfico).
- **Zonas seguras:** los textos respetan los márgenes de UI de Reels/Stories (~250 px arriba, ~350 px abajo).
- **Audio:** el video no incluye pista de audio; agrega música desde el gestor de Meta Ads o pide una versión con audio.
- **Thumbnail:** elige entre los frames de `previews/` (el del CTA, `preview_0435.png`, funciona bien).
- **CTA sugerido del botón:** "Más información" → `https://servicia.com.mx/`
- **Copy sugerido del anuncio:**
  > ¿Tu operación depende de gente que no llega y pendientes que nadie persigue?
  > Operamos tu piso y tu administración: gente + IA, SLA y tablero en vivo. Diagnóstico operativo en 90 días o menos.
  > 👉 Agenda tu diagnóstico en servicia.com.mx
