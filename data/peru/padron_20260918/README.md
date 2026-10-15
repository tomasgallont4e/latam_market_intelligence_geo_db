# Perú — Padrón MINEDU 2026-09-18

Agregado reproducible del archivo oficial `Padron_web.dbf`. Contiene oferta de
servicios/programas educativos por departamento y nivel, con conteos activos,
públicos y privados. No contiene matrícula, estudiantes, carrera/programa
académico ni matrícula universitaria; por ello no sustituye los indicadores
educativos de 2025 ni se interpreta como demanda.

Ejecutar:

```powershell
python scripts/build-peru-padron-2026.py <Padron_web.dbf> data/peru/padron_20260918
```
