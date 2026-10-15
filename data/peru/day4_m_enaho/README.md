# Perú — Día 4 — ENAHO 2025, capa M parcial

Agregados de personas ocupadas de ENAHO módulo 05, con factor `FAC500A`, por
departamento de residencia, división CIIU y código de banda de tamaño reportado.
El resumen departamental también distingue empleo cuyo trabajo/negocio/empresa
reporta hasta 20 personas (`P512A=1`) y empleo cuyo negocio declara registro
SUNAT (`P510A1=1` o `2`).

Los microdatos no se incluyen. Las filas describen empleo de personas, no
empresas, establecimientos, ventas, formalización legal ni un universo legal
de micronegocios. El tamaño y registro SUNAT son declaraciones de la persona
encuestada.

Ejecutar:

```powershell
python scripts/build-peru-day4-m-enaho.py <Enaho01a-2025-500.csv> data/peru/day4_m_enaho
```
