"""Build Peru Layer F deliverables (persona correspondence table B, source registry) from the run outputs.

Usage: python3 -I build_layer_f_deliverables_pe.py <out_dir_of_layer_f_epen_peru> <deliverable_dir>
"""
import csv, os, sys, json, shutil

OUT, DEL = sys.argv[1], sys.argv[2]
ENAHO_OUT = sys.argv[3] if len(sys.argv) > 3 else None
os.makedirs(DEL, exist_ok=True)

est = {r["group_id"]: r for r in csv.DictReader(open(os.path.join(OUT, "f_persona_estimates_pe.csv"), encoding="utf-8"))}
mp = list(csv.DictReader(open(os.path.join(OUT, "f_occupation_mapping_pe.csv"), encoding="utf-8")))

ALIAS = {3: "IT technicians and support", 4: "IT managers", 5: "Designers", 7: "Finance analysts",
         8: "Data and research specialists", 13: "University and IT educators"}

# justification / warnings per persona (written from the INEI CNO 2015 annexes 3-4 and CNO definitions)
NOTES = {
    1: ("exact_4digit_official_correspondence",
        "CNO 2511, 2512, 2513, 2519 and 2521 link only to CIUO 2511-2519. Codes differ from CIUO (CNO 2512 'Especialistas programadores' = CIUO 2514; CNO 2521 'Especialistas en soporte de sistemas' = CIUO 2511 per INEI).",
        "CNO 2511 'Analistas de sistemas' is 82% of the persona. CIUO 2512 (software developers) is reached only through CNO 2519 (Annex 4, relative link). Sensitivity without CNO 2521: -0.7%."),
    2: ("exact_4digit_official_correspondence",
        "CNO 2514 (=CIUO 2521), 2515 (=CIUO 2522+2523) and 2529 (=CIUO 2529).",
        "Only 5 records: point estimate suppressed. INEI coding concentrates IT professionals in CNO 2511. Use Personas 1+2 combined (COMB_P01_P02) as the robust reading."),
    3: ("exact_4digit_official_correspondence",
        "CNO 3511-3514, 3521, 3522 (same numbers as CIUO) plus CNO 3126 'Supervisores de servicios TIC' (INEI link to CIUO 3514 only).",
        "CNO 3521 (broadcasting/audiovisual technicians) is 28% of the persona. ICT-only subset (without 3521-3522) = sensitivity S3_ict_only."),
    4: ("exact_4digit_official_correspondence",
        "CNO 1330 = CIUO 1330 (absolute link).",
        "Only 13 records: suppressed. CNO 1150 'Directores generales del sector privado de servicios TIC' links to CIUO 1120 (not persona 4) and is reported only as informational (3 records)."),
    5: ("exact_4digit_official_correspondence_but_undercoverage",
        "CNO 2163 and 2166 = CIUO 2163, 2166 (absolute links).",
        "Only 9 records: suppressed. Peru codes most designers (interior, product, fashion, packaging) to CNO 3432 'Disenadores y decoradores', which INEI links to CIUO 3432 (technician level, outside the persona). CNO 3432 (63,189) is reported as informational outside any ring; it is not added to persona 5."),
    6: ("exact_4digit_official_correspondence_broader_national_scope",
        "CNO 2421 and 2422 = CIUO 2421, 2422 (absolute links).",
        "CNO 2421 explicitly includes 'Administrador de Empresas' and 'Otros administradores' (CNO 2015 p.128-129): in Peru it captures generic business administrators, broader than the ISCO-08 concept. Cannot be separated with 4-digit codes."),
    7: ("exact_4digit_official_correspondence",
        "CNO 2412 'Analistas y asesores financieros y de inversiones' = CIUO 2412 + 2413 (CNO has no 2413).",
        "Only 19 records: suppressed."),
    8: ("official_correspondence_includes_technician_codes",
        "CNO 2120, 2631, 2632 (absolute) + CNO 3315 and 3317 (INEI links only to CIUO 3314).",
        "CNO 3317 'Tecnicos en economia y afines' includes commerce/export assistants and marketing technicians (20,527; 41% of persona). Sensitivity without 3315+3317: 29,001. CNO 3313 (accounting technicians) excluded: primary link is CIUO 3313."),
    9: ("exact_4digit_official_correspondence",
        "CNO 2431, 2432 = CIUO 2431, 2432 (absolute links).",
        "30 unique persons, CV 24.5%: publish only as low-precision estimate."),
    10: ("exact_4digit_official_correspondence",
         "CNO 2411 = CIUO 2411 (absolute link).", "High confidence."),
    11: ("exact_4digit_official_correspondence",
         "CNO 2141-2146, 2149, 2151-2153 = same CIUO codes (absolute links).", "High confidence."),
    12: ("exact_4digit_official_correspondence_partial",
         "CNO 1211-1223, 1321-1324, 1341-1346 (same codes) + national openings CNO 1325, 1326, 1421 (INEI links to CIUO 1324).",
         "CIUO 1349 has no reliable CNO code: CNO 1499 'Otros gerentes de servicios' is linked to CIUO 1349 in Annex 4 but to CIUO 1439 in Annex 3 -> excluded (sensitivity S12_add_1499: +5,213). CNO 1345 (directors of education centres, incl. school principals) is 39% of the persona."),
    13: ("relative_links",
         "CNO 2311 'Profesores de universidades' (relative link to CIUO 2310, also to 2353-2355 language/music/arts teachers) + CNO 2353 'Instructores en TI' (= CIUO 2356).",
         "CNO 2312 'Profesores de educacion tecnico productiva' (CETPRO, not higher education) excluded (sensitivity +7,916). IT instructors alone (CNO 2353): 10 records, suppressed. Teachers of non-university higher-education institutes are not separately identifiable."),
}

rows = []
for p in range(1, 14):
    e = est[f"P{p:02d}"]
    m = [r for r in mp if int(r["template_persona_number"]) == p]
    prim = sorted(r["cno2015_code"] for r in m if r["in_primary"] == "True")
    excl = sorted(r["cno2015_code"] for r in m if r["mapping_status"] == "excluded_ambiguous")
    cls, just, warn = NOTES[p]
    rows.append(dict(
        template_persona_number=p, persona_canonical=e["label"], template_alias=ALIAS.get(p, ""), ring=e["ring"],
        isco08_template_codes=";".join(sorted({c for r in m for c in r["ciuo08_codes_in_persona"].split(";") if c})),
        cno2015_codes_primary=";".join(prim), cno2015_codes_excluded=";".join(excl), mapping_class=cls,
        records=e["records"], unique_persons=e["unique_persons"],
        employed_2025=e["employed"] if e["publication_status"] != "suppressed_unreliable" else "",
        cv=e["cv"] if e["publication_status"] != "suppressed_unreliable" else "",
        share_of_employed=e["share_of_employed"] if e["publication_status"] != "suppressed_unreliable" else "",
        template_confidence=e["template_confidence"], publication_status=e["publication_status"],
        justification=just, warnings=warn))
with open(os.path.join(DEL, "f_persona_correspondence_pe.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), quoting=csv.QUOTE_NONNUMERIC)
    w.writeheader(); w.writerows(rows)

meta = json.load(open(os.path.join(OUT, "f_run_meta_pe.json")))
SRC = [
    dict(source_id="SRC_INEI_EPEN_2025_DPTO", source_name="EPEN 2025 - Departamentos, base anual (enero-diciembre)", publisher="INEI",
         dataset_version="Modulo 1001-Modulo76; EPEN 2025 BD_Publicacion Dpto.csv", reference_period="2025-01..2025-12",
         url="https://proyectos.inei.gob.pe/microdatos/", access="Supplied by Think4ever 2026-10-09 (1001-Modulo76.zip)",
         sha256=meta["epen_sha256"], zip_sha256="eea0b593ace04f00b6d795fd4eb7b5d8d3f2d9d856037f5c86d74d2d10909f7a",
         role="Layer F primary microdata (local only, not redistributed)", license_status="unverified; redistribution not assumed"),
    dict(source_id="SRC_INEI_EPEN_2025_DIC", source_name="EPEN 2025 Diccionario de variables, 4to trimestre (oct-dic 2025)", publisher="INEI",
         dataset_version="Lima, febrero 2026", reference_period="2025Q4", url="https://proyectos.inei.gob.pe/microdatos/",
         access="Supplied by Think4ever (Diccionario.zip)", sha256="", zip_sha256="ad73fa7158bd2e9b31a8841a37fb41e466f796a40a061068751a54edfcbe0a56",
         role="Variable definitions. Quarterly dictionary: does not document CCDD, FAC300_ANUAL, Informal_P of the annual base", license_status="unverified"),
    dict(source_id="SRC_INEI_EPEN_2025_FICHA", source_name="EPEN 2025 Ficha tecnica", publisher="INEI", dataset_version="Lima, enero 2025 (signed 13.02.2025)",
         reference_period="2025", url="https://proyectos.inei.gob.pe/microdatos/", access="Supplied by Think4ever (Ficha_Tecnica.zip)", sha256="",
         zip_sha256="36cf216f074118e40e98a7d6b8247b3c3e3f607982c8d11bdd76023f373426a8",
         role="Coverage, design (stratified, 2-stage, independent by department; 142,084 dwellings), inference levels", license_status="unverified"),
    dict(source_id="SRC_INEI_CNO2015", source_name="Clasificador Nacional de Ocupaciones 2015 (CNO 2015), incl. Anexos 3-4 CNO 2015 <-> CIUO 2008",
         publisher="INEI", dataset_version="2015 (472 pp.)", reference_period="", url="https://www.inei.gob.pe/media/Clasificador_Nacional_de_Ocupaciones_2015.pdf",
         access="Supplied by Think4ever", sha256="3624406d554d0af1374a1b968bd18d6b1a8abfeb320717f1ab58d9b49e18b125", zip_sha256="",
         role="Occupation classifier and official 4-digit correspondence with CIUO-08", license_status="public document"),
    dict(source_id="SRC_INEI_EPEN_ANUAL_2025_PRESS", source_name="INEI informe tecnico 'Peru: Comportamiento de los indicadores del mercado laboral a nivel nacional y en 27 ciudades' 2025 (as reported by Andina / El Peruano, 15-02-2026)",
         publisher="INEI (via Agencia Andina, El Peruano)", dataset_version="", reference_period="2025 and 2025Q4",
         url="https://andina.pe/agencia/noticia-inei-poblacion-ocupada-aumento-15-el-ano-2025-a-nivel-nacional-1063201.aspx ; https://elperuano.pe/noticia/289261-inei-poblacion-ocupada-aumento-15-en-el-ano-2025-a-nivel-nacional",
         access="read online 2026-10-09; INEI original (gob.pe) not reachable from this environment", sha256="", zip_sha256="",
         role="Secondary corroboration (superseded by SRC_INEI_EPEN_IT_ANUAL_2025 for levels); still the source for Q4 17,834.8k, unemployment by sex (M 4.2%, W 5.7%) and Lima income S/ 2,486.0", license_status="secondary report of official figures"),
    dict(source_id="SRC_INEI_EPEN_IT_ANUAL_2025", source_name="INEI, 'Peru: Comportamiento de los indicadores del mercado laboral a nivel nacional y en 27 ciudades' - enero-diciembre 2025 y IV trimestre 2025",
         publisher="INEI", dataset_version="febrero 2026 (Informe Tecnico number not stated in the document)", reference_period="2025; 2025Q4",
         url="https://www.inei.gob.pe/media/MenuRecursivo/boletines/01-informe-tecnico-empleo-nacional.pdf",
         access="read online directly from inei.gob.pe 2026-10-09 (WebFetch); PDF not downloadable from this environment, so no file hash",
         sha256="", zip_sha256="",
         role="PRIMARY control totals: employed 17,575.2k (urban 14,287.0k, rural 3,288.1k; men 9,751.5k, women 7,823.7k); size 1-10/11-50/51+ 12,601.3/1,381.4/3,592.4k; branches; unemployed 902.1k; unemployment 4.9% (urban 5.7%, rural 1.4%); informality 70.2%",
         license_status="public"),
    dict(source_id="SRC_INEI_EPEN_2024_IT", source_name="INEI informe tecnico EPEN IV trimestre 2024 (annual 2024) and I trimestre 2025", publisher="INEI", dataset_version="",
         reference_period="2024; 2025Q1", url="https://www.inei.gob.pe/media/MenuRecursivo/boletines/informe-tecnico_empleonacional.pdf ; https://www.inei.gob.pe/media/MenuRecursivo/boletines/informe-tecnico_empleonacional_1.pdf",
         access="read online", sha256="", zip_sha256="", role="Control totals: 2024 urban/rural levels (+2025 changes); 2025Q1 employed 17,374.0k", license_status="public"),
    dict(source_id="REQ_INEI_EPEN_2025_ANUAL_DIC", source_name="Diccionario de la base anual EPEN 2025 Departamentos (documenting CCDD, FAC300_ANUAL, Informal_P)", publisher="INEI",
         dataset_version="", reference_period="2025", url="https://proyectos.inei.gob.pe/microdatos/ (EPEN - Departamentos - 2025 - Anual - Diccionario); tried https://www.inei.gob.pe/media/DATOS_ABIERTOS/EPEN_DEP/DICCIONARIO/2025/... (not reachable)",
         access="open request: the supplied Diccionario.zip is the 4th-quarter 2025 dictionary, not the annual one", sha256="", zip_sha256="",
         role="Confirms annual-base variables. Precedent: the EPEN 2022 annual dictionary (SRC_INEI_EPEN_2022_ANUAL_DIC) defines FAC300_ANUAL = 'Factor anual nacional de empleo' and CCDD = 'Codigo del departamento' (01-25)", license_status=""),
    dict(source_id="SRC_INEI_EPEN_2022_ANUAL_DIC", source_name="EPEN Diccionario de variables 2022 (base anual departamental)", publisher="INEI", dataset_version="2022", reference_period="2022",
         url="https://www.inei.gob.pe/media/DATOS_ABIERTOS/EPEN_DEP/DICCIONARIO/2022/Diccionario.pdf", access="read online 2026-10-09", sha256="", zip_sha256="",
         role="Precedent for annual-base variable definitions (FAC300_ANUAL, CCDD, CODCIUDAD); C308_COD described only as 'Segun Codigo de Ocupaciones'", license_status="public"),
    dict(source_id="SRC_INEI_ENAHO_2024_Q01A", source_name="ENAHO 2024 cuestionario ENAHO 01A (Educacion, Salud y Empleo)", publisher="INEI", dataset_version="2024", reference_period="2024",
         url="https://proyectos.inei.gob.pe/iinei/srienaho/Descarga/DocumentosMetodologicos/2024-55/9_CUESTIONARIO-ENAHO01A.pdf", access="read online 2026-10-09", sha256="", zip_sha256="",
         role="ENAHO evaluation: P517 = secondary-occupation category (not place of work); no telework/place-of-work question", license_status="public"),
    dict(source_id="SRC_3P_ENAHO2025_INVENTORY", source_name="IchiSieben/enaho-ingresos-informalidad, reports/inventario_columnas.csv (third party, not official)", publisher="third party (GitHub)",
         dataset_version="git clone --depth 1, 2026-10-09", reference_period="2025", url="https://github.com/IchiSieben/enaho-ingresos-informalidad", access="git clone (read-only)", sha256="", zip_sha256="",
         role="ENAHO evaluation only: evidence that ENAHO 2025 (survey 1031) modules 02/03/05/34 exist and list their columns (P505R4, FAC500A, ESTRSOCIAL...)", license_status="not used as data"),
    dict(source_id="REQ_INEI_EPEN_2025_C318A", source_name="EPEN 2025 variable C318A (lugar de trabajo) - not in the public base", publisher="INEI", dataset_version="", reference_period="2025",
         url="Solicitud de acceso a la informacion (Ley 27806) to INEI", access="open request (proposed)", sha256="", zip_sha256="", role="Only identified source for F10 (works from home)", license_status=""),
    dict(source_id="SRC_INEI_ENAHO_2025_M05", source_name="ENAHO 2025 modulo 05 Empleo e ingresos (Enaho01a-2025-500.csv), encuesta 1031", publisher="INEI",
         dataset_version="1031-Modulo05 (files dated 2026-04-28/29)", reference_period="2025-01..2025-12", url="https://proyectos.inei.gob.pe/microdatos/",
         access="Supplied by Think4ever 2026-10-09 (1031-Modulo05.zip)", sha256="88c11d066244eac1f5b263188a4d6d160a6b534f6b6c12344f6c2946524e683d", zip_sha256="bb03e04ed13cd7e839df568b75e8afae3b496d4adcf78ff739f99a5340eea8a6",
         role="F9 and F1 diagnostic (ENAHO results kept separate from EPEN); P505R4 = CNO 2015 (dictionary), FAC500A, OCU500", license_status="unverified; redistribution not assumed"),
    dict(source_id="SRC_INEI_ENAHO_2025_SUMARIA", source_name="ENAHO 2025 modulo 34 Sumaria 8 grupos de gasto (Sumaria-2025.csv)", publisher="INEI",
         dataset_version="1031-Modulo34", reference_period="2025", url="https://proyectos.inei.gob.pe/microdatos/", access="Supplied by Think4ever 2026-10-09 (1031-Modulo34.zip)",
         sha256="ff0a86c50c18f8813f7a11a95b4d95aacc7ae94a67fb49fc457683c4b9df2e61", zip_sha256="c762a7fd60ffd77fd93ee05a98f711055a0e81a109f6666a73969a9905cea123", role="Household real per-capita income (ipcr_0) and national population quintiles; ESTRSOCIAL; POBREZA controls. Chosen over Sumaria-2025-12g (sha256 8a0748c58cd20591...) because the official INEI do-file uses 8-group variables (D-PE-07)",
         license_status="unverified; redistribution not assumed"),
    dict(source_id="SRC_INEI_ENAHO_2025_DOCS", source_name="ENAHO 2025 Diccionario_2025.pdf, FichaTecnica.pdf, CED-01A-500-2025.pdf (cuestionario modulo 500), Estratificacion_del_Marco.pdf, ENAHO-TABLA-CNO-2015.csv",
         publisher="INEI", dataset_version="abril-mayo 2026", reference_period="2025", url="https://proyectos.inei.gob.pe/microdatos/", access="inside the supplied ZIPs",
         sha256="dic b91dc84e9233d4c9; ficha 365f77d40bd23853; ced c37513d972cd620a; estratificacion 04de53a634646355; cno cc0b5f15e971cc11", zip_sha256="",
         role="Variable definitions, design (36,594 dwellings; inference: national, urban/rural, 24 departments, natural regions, Lima Metropolitana), ESTRSOCIAL definition, CNO 2015 code list (473 = PDF list)", license_status="public documentation"),
    dict(source_id="SRC_INEI_ENAHO_2025_CONSTVARGASTO", source_name="ConstVarGasto-Metodologia actualizada_2025 (01_ConstrVarGastoIngreso2015-2025.do; deflactores_base2025_new.dta; despacial_ldnew.dta)",
         publisher="INEI", dataset_version="2026", reference_period="2015-2025", url="inside 1031-Modulo34.zip", access="supplied", sha256="d12198be5d6f0cf334e301797b7ecc7db0b4b3509cb9d2c87b176d630d2d3447", zip_sha256="",
         role="Official formula of real per-capita monthly income ipcr_0 = sum of components /(12*mieperho*ld*i00); weight factor07*mieperho", license_status="public"),
    dict(source_id="SRC_INEI_POBREZA_2025_PRESS", source_name="INEI pobreza monetaria 2025 (as reported by El Peruano, Infobae, Energiminas, 05-05-2026; INEI note gob.pe/institucion/inei/noticias/1387366)",
         publisher="INEI (via press)", dataset_version="mayo 2026", reference_period="2025",
         url="https://elperuano.pe/noticia/295035-inei-pobreza-se-redujo-en-19-en-el-2025-y-afecta-al-257-de-peruanos ; https://www.infobae.com/peru/2026/05/05/la-pobreza-en-peru-se-reduce-a-257-en-2025-pero-1-de-cada-3-podria-caer-en-cualquier-momento-segun-inei/ ; https://energiminas.com/2026/05/05/inei-pobreza-monetaria-alcanzo-al-257-de-la-poblacion-en-peru-durante-2025/",
         access="read online 2026-10-09", sha256="", zip_sha256="", role="Secondary corroboration of ENAHO controls (superseded by SRC_INEI_POBREZA_2016_2025_ANEXO); still the only source for vulnerable 32.8% and extreme poor 1,614k",
         license_status="secondary report of official figures"),
    dict(source_id="SRC_INEI_POBREZA_2016_2025_IT", source_name="INEI, 'Peru: Evolucion de la Pobreza Monetaria, 2016-2025' - Informe Tecnico (425 pp.)", publisher="INEI",
         dataset_version="PDF created 2026-05-04, modified 2026-05-05; gob.pe publication 8088591", reference_period="2016-2025",
         url="https://www.gob.pe/institucion/inei/informes-publicaciones/8088591-peru-evolucion-de-la-pobreza-monetaria-2016-2025",
         access="Supplied by Think4ever 2026-10-09 (8088591-peru-evolucion-de-la-pobreza-monetaria-2016-2025.pdf)",
         sha256="475cc9c6b9c3539eef644a0b19551f0974cb78430777520b0a56f2869cadfe9c", zip_sha256="",
         role="Official 2025 figures: real per-capita income S/ 1 252 (section 2.2, Grafico 2.17); expenditure S/ 920; sample design (cap. 9.2). Does not state the variance strata specification", license_status="public"),
    dict(source_id="SRC_INEI_POBREZA_2016_2025_ANEXO", source_name="INEI, Anexo Estadistico en Excel (Evolucion de la Pobreza Monetaria 2016-2025): 01_Ingresos (I.15-I.22), 01_Gastos, 02_Lineas, 03_FGT, 04_Perfil",
         publisher="INEI", dataset_version="gob.pe publication 8088591", reference_period="2016-2025",
         url="https://www.gob.pe/institucion/inei/informes-publicaciones/8088591-peru-evolucion-de-la-pobreza-monetaria-2016-2025",
         access="Supplied by Think4ever 2026-10-09 (8088591-anexo-estadistico-en-exce.zip)", sha256="01_Gastos reales_nominales_2016_2025_informe.xlsx: 6b819d46b8e91eddaaee0122b2674a52e352fba1f0bbfa328d625fc7484b1d69; 01_Ingresos Reales_nominales_ 2016-2025_informe.xlsx: 497e71c79b27cd4acfea02e173635ab9e92ffff067f557862b457eeb184fbf23; 02_Lineas Total y Extrema 2016-2025_informe.xlsx: a2153b27ab89b2af61b1b33439ac597372f0756d7fb4003525ab7ac24223578e; 03_FGT de Pobreza 2016-2025_informe.xlsx: eac168953a0d2f085bf296de7a8fc6a422d7ea9e75b691e25257fa4970f0f47b; 04_Perfil_pobreza 2016_2025_informe.xlsx: a0e2c7eebbbdb487eb69a41b13e9b262d3cb73b560234ccf639d2771326ea8bf",
         zip_sha256="d17ba9bd74928629e446b83d27b5648f0342338072b3bb1dfbe7be7f5ce606c4",
         role="V1 validation: I.17 2025 national 1 252.345, SE 12.08266, min 1 228.661, max 1 276.029 (+12 domains); III.1 poverty, III.4 extreme poverty, I.1 expenditure", license_status="public"),
]
with open(os.path.join(DEL, "source_registry_layer_f_pe.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(SRC[0].keys()), quoting=csv.QUOTE_NONNUMERIC)
    w.writeheader(); w.writerows(SRC)
for fn in os.listdir(OUT):
    shutil.copy(os.path.join(OUT, fn), os.path.join(DEL, fn))

# ---- approved decisions (2026-10-09): suppression in publishable tables; persona 8 scope notes
SCOPE = {
    "P08": "Broad occupational category (approved D-PE-05 primary estimate): includes technician codes CNO 3315 and 3317 (commerce/export/marketing technicians via the official INEI link to CIUO 3314); not limited to specialised data and research professionals.",
    "S8_excl_3315_3317": "Restricted scenario (approved D-PE-05): professionals only, CNO 2120, 2631, 2632.",
    "P06": "CNO 2421 includes 'Administrador de Empresas' and 'Otros administradores': broader than ISCO-08 2421.",
    "INFO_3432": "Informational only; not persona 5 and not in any ring.",
    "INFO_DESIGN_2163_2166_3432": "D-PE-09 informational designers group (professional 2163/2166 + technician 3432); not persona 5; not in any ring; not additive to ring totals.",
    "INFO_2163": "Code-level informational (D-PE-09).", "INFO_2166": "Code-level informational (D-PE-09).",
}
UNIT = "occupational_population (employed persons whose main job is in the group); not TAM/SAM/SOM, not confirmed or potential users"
VALS = ["employed", "se", "cv", "ci95_low", "ci95_high", "share_of_employed", "share_se"]
full = list(csv.DictReader(open(os.path.join(OUT, "f_persona_estimates_pe.csv"), encoding="utf-8")))
pub = []
supp = set()
for r in full:
    r = dict(r)
    r["scope_note"] = SCOPE.get(r["group_id"], "")
    r["measure"] = UNIT
    if r["publication_status"] == "suppressed_unreliable":
        supp.add(r["group_id"])
        for v in VALS:
            r[v] = ""
    pub.append(r)
with open(os.path.join(DEL, "f_persona_estimates_pe.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(pub[0].keys())); w.writeheader(); w.writerows(pub)
os.makedirs(os.path.join(DEL, "..", "validation", "internal_not_publishable"), exist_ok=True)
shutil.copy(os.path.join(OUT, "f_persona_estimates_pe.csv"),
            os.path.join(DEL, "..", "validation", "internal_not_publishable", "f_persona_estimates_internal_pe.csv"))
prof = list(csv.DictReader(open(os.path.join(OUT, "f_persona_profiles_pe.csv"), encoding="utf-8")))
status = {r["group_id"]: r["publication_status"] for r in full}
for r in prof:
    r["group_publication_status"] = status.get(r["group_id"], "")
    if r["group_id"] in supp:
        r["value"] = ""; r["weighted_numerator"] = ""
with open(os.path.join(DEL, "f_persona_profiles_pe.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(prof[0].keys())); w.writeheader(); w.writerows(prof)
# code-level tables: same rule (no CV per code) -> blank weighted figure when < 30 records
for fn, wcol in [("f_cno_code_counts_pe.csv", "employed"), ("f_occupation_mapping_pe.csv", "weighted_employed")]:
    rr = list(csv.DictReader(open(os.path.join(OUT, fn), encoding="utf-8")))
    nc = "records" if "records" in rr[0] else "sample_records"
    for r in rr:
        small = int(float(r[nc] or 0)) < 30
        r["code_cell_status"] = "suppressed_lt30_records" if small else "publish_code_level_no_cv"
        if small:
            r[wcol] = ""
    with open(os.path.join(DEL, fn), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rr[0].keys())); w.writeheader(); w.writerows(rr)
    shutil.copy(os.path.join(OUT, fn), os.path.join(DEL, "..", "validation", "internal_not_publishable", fn.replace("_pe.csv", "_internal_pe.csv")))

# aggregate integrity: rings still contain suppressed personas' codes
rings = {r["group_id"]: set(r["cno2015_codes"].split(";")) for r in full}
for g, ring in [("P02", "RING_CORE"), ("P04", "RING_CORE"), ("P05", "RING_ADJACENT"), ("P07", "RING_ADJACENT")]:
    assert rings[g] <= rings[ring], (g, ring)
DEC = [
    ("D-PE-01", "2026-10-09", "EPEN 2025 primary Layer F source; ENAHO 2025 complementary", "approved (provisional, verified 2026-10-09)", "Classifier, coverage and weights verified; 24/24 INEI control checks pass"),
    ("D-PE-03", "2026-10-09", "Suppression: CV > 30% or < 30 unique persons -> suppressed; CV 15-30% -> low precision", "approved",
     "Suppressed values removed from publishable tables (data/); kept in validation/internal_not_publishable and inside ring/combined aggregates"),
    ("D-PE-04", "2026-10-09", "Exclude CNO 1499 (P12), 2312 (P13), 3313 (P8) from primary mapping; keep sensitivities", "approved", "S12_add_1499, S13_add_2312, S8_add_3313"),
    ("D-PE-05", "2026-10-09", "Persona 8 primary = 50,235 (broad category incl. technicians); restricted professionals scenario = 29,001", "approved with warning",
     "Neither figure describes confirmed or potential users"),
    ("D-PE-06", "2026-10-09", "ENAHO 2025 for F6 (detailed geography), F9, F10", "authorised for evaluation only", "No pooling of ENAHO and EPEN weights; no cross-survey extrapolation"),
    ("D-PE-07", "2026-10-09", "Use Sumaria-2025 (8 grupos) for income quintiles, not Sumaria-2025-12g", "applied (methodological; within D-PE-06 mandate)",
     "INEI do-file uses 8-group variables; household income variables identical in both files (max diff S/ 0.008)"),
    ("D-PE-08", "2026-10-09", "F9 computed from ENAHO 2025 as a separate source (quintiles of ipcr_0 + ESTRSOCIAL); F1 from ENAHO only as diagnostic", "applied; pending final validation",
     "No pooling of FAC500A and FAC300_ANUAL; no ENAHO shares applied to EPEN totals"),
    ("D-PE-09", "2026-10-09", "Designers: informational group CNO 2163+2166+3432 in EPEN and ENAHO, outside the 13 personas and the rings (option B)", "approved as informational analysis",
     "Persona 5 unchanged (EPEN suppressed; ENAHO 60,305 kept as separate ENAHO result); ring aggregates unchanged. EPEN reserves 2163/2166 for university graduates (100%) and codes other designers to 3432 (19.8% university)"),
    ("D-PE-10", "2026-10-09", "F9 from ENAHO 2025 incorporated in DRAFT as a separate source", "provisionally approved",
     "Final approval pending: official mean real per-capita income check (INEI report 2016-2025 not reachable from this environment); design specification verified by sensitivity"),
    ("D-PE-11", "2026-10-09", "F6 = EPEN geography (department + Lima Metropolitana y Callao); F10 = pending official information (EPEN C318A not public; absent in ENAHO 2025)", "approved",
     "No F10 estimate produced"),
    ("D-PE-12", "2026-10-09", "ENAHO variance specification aligned with INEI: PSU = CONGLOME, no strata", "applied",
     "Official annex I.17 (13 domains): PSU-only SE = 1.000-1.048x official (median 1.008); dept x ESTRATO gave 0.883-1.000x (CIs too narrow). No F9 publication-status changes. EPEN keeps dept x ESTRATO (no official SE to calibrate against)"),
    ("V1", "2026-10-09", "Mean real per-capita income vs INEI official (annex I.17)", "VALIDATED",
     "1,252.345 vs 1,252.345 official; 13 domains, poverty, extreme poverty and expenditure reproduced to <= 0.001 (expenditure 0.03)"),
    ("D-PE-10b", "2026-10-09", "F9 (ENAHO 2025, separate source) final approval", "APPROVED (Layer F remains DRAFT)", "Authorised by Think4ever 2026-10-09 subject to V1 and documentary review; SE alignment D-PE-12 applied"),
    ("CLOSE-PE-D1", "2026-10-09", "Peru Day 1 (Layers A, B and F) declared FINAL", "AUTHORISED by Think4ever 2026-10-09 19:06 (America/Bogota)",
     "Documentary and methodological closure; not an approval of potential-market estimates or commercial recommendations. Results unchanged"),
    ("D-03/D-04", "2026-10-09", "A4 threshold and A5 definition", "kept provisional (Layer A unchanged)", ""),
]
with open(os.path.join(DEL, "decisions_log_pe.csv"), "w", newline="", encoding="utf-8") as f:
    SUPERSEDED = {"D-PE-01": "Confirmed by EPEN audit (24/24 INEI controls)", "D-PE-06": "D-PE-08 / D-PE-10b", "D-PE-08": "D-PE-10b",
                  "D-PE-10": "D-PE-10b"}
    w = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
    w.writerow(["decision_id", "date", "decision", "status", "note", "current", "superseded_by"])
    w.writerows([list(d) + [d[0] not in SUPERSEDED, SUPERSEDED.get(d[0], "")] for d in DEC])
print("ok", len(rows))

# ---- ENAHO (separate source) outputs
if ENAHO_OUT:
    for fn in ["f9_persona_socioeconomic_enaho_pe.csv", "f1_enaho_diagnostic_pe.csv", "enaho_quintile_cutpoints_pe.csv"]:
        shutil.copy(os.path.join(ENAHO_OUT, fn), os.path.join(DEL, fn))
    # D-PE-09 designers informational comparison (rows by source; never combined)
    f1e = list(csv.DictReader(open(os.path.join(ENAHO_OUT, "f1_enaho_diagnostic_pe.csv"), encoding="utf-8")))
    epn = {r["group_id"]: r for r in full}
    rows_d = []
    for gid in ["INFO_2163", "INFO_2166", "INFO_3432", "INFO_DESIGN_2163_2166_3432", "P05"]:
        r = epn[gid]; sup = r["publication_status"] == "suppressed_unreliable"
        rows_d.append(dict(group_id=gid, source="EPEN 2025", cno2015_codes=r["cno2015_codes"], records=r["records"], unique_persons=r["unique_persons"],
                           employed=("" if sup else r["employed"]), cv=("" if sup else r["cv"]), ci95_low=("" if sup else r["ci95_low"]),
                           ci95_high=("" if sup else r["ci95_high"]), status=r["publication_status"],
                           in_rings=("persona 5 (Adjacent)" if gid == "P05" else "no")))
        e = next(x for x in f1e if x["group_id"] == gid)
        rows_d.append(dict(group_id=gid, source="ENAHO 2025", cno2015_codes=r["cno2015_codes"], records=e["records"], unique_persons=e["unique_persons"],
                           employed=e["enaho_employed"], cv=e["enaho_cv"], ci95_low=e["enaho_ci95_low"], ci95_high=e["enaho_ci95_high"],
                           status={"diagnostic": "publish_enaho_separate", "diagnostic_low_precision": "publish_low_precision_enaho_separate"}.get(e["status"], e["status"]),
                           in_rings=("persona 5 (Adjacent) - ENAHO result, separate" if gid == "P05" else "no")))
    with open(os.path.join(DEL, "f_designers_informational_pe.csv"), "w", newline="", encoding="utf-8") as fh:
        wd = csv.DictWriter(fh, fieldnames=list(rows_d[0].keys())); wd.writeheader(); wd.writerows(rows_d)
    for fn in ["enaho_sumaria_checks_pe.csv", "enaho_sumaria_meta_pe.json", "enaho_f9_meta_pe.json", "enaho_vs_inei_official_validation_pe.csv"]:
        shutil.copy(os.path.join(ENAHO_OUT, fn), os.path.join(DEL, "..", "validation", fn))
