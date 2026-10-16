# Revisión de integridad

Importado desde `peru_consolidado_geodb.zip` el 2026-10-16.

Se verificaron los SHA-256 de los nueve CSV de datos y de `meta_sources.csv`: todos coinciden con el paquete entregado. El paquete original incluía una entrada de `manifest.csv` con un hash que no correspondía a su contenido final. Para evitar un manifiesto autorreferencial imposible de verificar, los manifiestos versionados aquí enumeran únicamente los artefactos de datos y metadatos, y no se incluyen a sí mismos.

No se modificó ningún valor de los CSV. Los valores `NULL` y los bloques marcados como bloqueados en `diccionario.md` se preservan tal como fueron entregados.
