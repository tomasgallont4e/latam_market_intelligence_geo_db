# Perú · Día 2 · capas G y H

Resultados reproducibles para las capas de empleo TI por industria (G) y
persona × geografía × comprador (H). Se generan con:

```powershell
$py = 'C:\\Users\\gutty\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe'
& $py scripts/build-peru-day2-gh.py <EPEN-2025-Modulo76.csv> <CNO-CIUO.csv> data/peru/day2_gh
```

## Publicación y límites

- Fuente: INEI, EPEN 2025, base anual por departamentos, módulo 76; las
  definiciones ocupacionales usan la correspondencia oficial CNO 2015–CIUO-08.
- La plantilla pide ciudad. La fuente ponderada reproducible disponible tiene
  dominio **departamental**. Cada fila se marca `department_proxy`; no es una
  cifra de ciudad ni se extrapola a distritos.
- G1–G3 cubren P01–P04 (cuatro personas TIC); G4 es el grupo de comparación de
  otras ocupaciones en empleo público, y no se presenta como personal TI.
- H usa `buyer_proxy` derivado de la posición laboral EPEN C310/C311. Es el
  sector del empleador, no demanda, compradores, TAM, SAM ni SOM.
- Las celdas directas con menos de 30 registros muestrales quedan como `null`.
  Un nulo no equivale a cero.

`fact_persona_department_epen2025.json` se copia además a `data/peru-map/`
para que el mapa muestre el núcleo TIC combinado y P01–P04 como mediciones
departamentales observadas, en lugar de la asignación modelada que se conserva
para P05–P13.
