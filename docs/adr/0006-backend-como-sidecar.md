# ADR 0006 · Microservicios empaquetados como un sidecar local

**Estado:** aceptada

## Contexto
El equipo trabaja con microservicios, pero la investigadora debe instalar la app como cualquier programa, sin Python ni Docker.

## Decisión
Cada servicio es un paquete con su propia API y contratos. `cip-sidecar` los levanta en un solo proceso local (puertos 8000–8003, solo `127.0.0.1`), PyInstaller lo convierte en `cip-backend.exe` y Tauri lo empaqueta como *sidecar*. En servidor, los mismos paquetes corren como contenedores (`compose.yaml`).

## Consecuencias
- Fronteras de servicio reales (HTTP + contratos) sin costo de operación en la laptop.
- El mismo código corre en la laptop o en un servidor del CIP.
- El ejecutable pesa ~40 MB; se podría reducir con el modo *onedir* y excluyendo dependencias opcionales.

## Alternativas
- **Monolito**: más simple de empaquetar, pero acopla agentes, ingesta y documentos.
- **Docker en la laptop**: inaceptable para una investigadora.
