#!/usr/bin/env python3
"""Extracción estructurada de la Descripción Comercial (Veritrade).
   [VERSIÓN COMPLETA - CON CATEGORÍA WITHMORY Y NUEVAS MARCAS]

FILTROS: SOLO estado NUEVO | SOLO kilometraje <= 100 km
EXCLUYE: motos, trimotos, vehículos L5/L6 (subterráneos, mini dumpers)
MANTIENE: TODOS los volquetes (pesados, livianos, mineros) y TODOS los camiones
INCLUYE: categoría_withmory (TRACTOCAMIÓN, VOLQUETE, CATEGORIA_PESO)
"""
from __future__ import annotations

import re, argparse, sys
from pathlib import Path
import pandas as pd, numpy as np
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

INPUTS_DIR, OUTPUTS_DIR, HEADER_ROW = "inputs", "outputs", 6

HARD_COLS = {
    "Partida Aduanera":"partida","Aduana":"aduana","DUA / DAM":"dua_dam","Fecha":"fecha_dua",
    "Importador":"importador","Embarcador / Exportador":"exportador","Kg Bruto":"kg_bruto",
    "Kg Neto":"kg_neto","Qty 1":"qty_1","Und 1":"und_1","Qty 2":"qty_2","Und 2":"und_2",
    "U$ FOB Tot":"fob_usd","U$ CFR Tot":"cfr_usd","U$ CIF Tot":"cif_usd",
    "Pais de Origen":"pais_origen","Pais de Compra":"pais_compra","Puerto de Embarque":"puerto_embarque",
    "Via":"via","Agente de Aduana":"agente_aduana","Estado":"estado","Ad Valorem":"ad_valorem",
    "IGV":"igv","ISC":"isc","IPM":"ipm","Fecha Embarque":"fecha_embarque",
    "Descripcion Comercial":"_descripcion",
}

CODES = {
    "MARCA":("marca","text"),"MODELO":("modelo","text"),"VERSION":("version","text"),
    "AÑO MOD":("anio_modelo","int"),"AÑO":("anio_modelo","int"),"VI":("vin","text"),
    "CH":("chasis","text"),"MO":("motor_serie","text"),"CO":("combustible","text"),
    "COMB":("combustible","text"),"C1":("color","text"),"NC":("num_cilindros","int"),
    "CC":("cilindrada_cc","num"),"PM":("potencia","power"),"EJ":("ejes","int"),
    "FR":("traccion","text"),"TT":("transmision","text"),"CA":("carroceria","text"),
    "AS":("asientos","int"),"PA":("puertas","int"),"PB":("peso_bruto","num"),
    "PN":("peso_neto","num"),"CU":("carga_util","num"),"LA":("largo_mm","num"),
    "AN":("ancho_mm","num"),"AL":("alto_mm","num"),"DE":("dist_ejes","num"),
    "KILOMETRAJE":("kilometraje","num"),
    "CLASIFICACION":("clasificacion","text"),
    "CAJA":("caja","text"),
    "MODELO_FLAG":("modelo_flag","text"),
}

EXTRACTED_ORDER = [
    "año_dua","mes_dua","trimestre_dua","categoria","categoria_peso","marca",
    "submarca_sinotruk","modelo","version","anio_modelo","vin","chasis","motor_serie",
    "combustible","color","num_cilindros","cilindrada_cc","potencia","potencia_hp",
    "ejes","traccion","transmision","carroceria","es_volquete_pesado","asientos","puertas",
    "peso_bruto","peso_neto","carga_util","largo_mm","ancho_mm","alto_mm","dist_ejes",
    "kilometraje","tipo_importador_sinotruk","desc_prefijo",
    "clasificacion",
    "caja",
    "modelo_flag",
    "categoria_withmory",
]

ESTADOS_NUEVOS = ["NUEVO","NUEVA","NEW","NUEVO/0 KM","0 KM","SIN USO","NUEVO SIN USO","NUEVA SIN USO","NUEVO DESARMADO","NUEVO SEMIARMADO"]
KM_MAX_NUEVO = 100

PESO_CATEGORIAS = {
    "LDT 1":(3500,5999),"LDT 2":(6000,9999),"MDT 1":(10000,14999),"MDT 2":(15000,16999),
    "MDT 3":(17000,24999),"SEMI PESADO":(25000,32999),"PESADO":(33000,float('inf')),
}

VOLQUETE_PESADO_MIN_KG = 25000
TRIMESTRES = {1:"Q1 (Ene-Mar)",2:"Q2 (Abr-Jun)",3:"Q3 (Jul-Sep)",4:"Q4 (Oct-Dic)"}

# ====================================================================
# ========== CARROCERÍAS A EXCLUIR (SOLO MOTOS Y SIMILARES) ==========
# ====================================================================
CARROCERIAS_EXCLUIR = [
    "TRIMOTO CARGA", "TRIMOTO", "MOTOCAR", "MOTOTAXI", "MOTO CARGA",
    "MOTO", "CUATRIMOTO", "TRICICLO", "TRICIMOTO",
    "MOTO FORM", "CARMELI MOTORS", "MOTOS ARMOT", "AB MOTORS",
    "KEANE MOTORS", "KAMA", "CK MOTORS", "BEEMOTOR", "FURINKAZAN",
]

# ====================================================================
# ========== SINOTRUK ==========
# ====================================================================
SINOTRUK_SUBMARCAS = {
    "SINOTRUK": "SINOTRUK",
    "SINOTRUCK": "SINOTRUK",
    "SITRAK": "SINOTRUK SITRAK",
    "HOWO": "SINOTRUK HOWO",
    "HOWO MAX": "SINOTRUK HOWO",
    "SINOTRUK HOWO": "SINOTRUK HOWO",
    "SINOTRUK SITRAK": "SINOTRUK SITRAK",
    "SINOTRUK HONAN": "SINOTRUK HONAN",
    "HONAN": "SINOTRUK HONAN",
    "HOMAN": "SINOTRUK HONAN",
    "SINOTRUK WANGPAI": "SINOTRUK WANGPAI",
    "WANGPAI": "SINOTRUK WANGPAI",
}

IMPORTADORES_SINOTRUK = {
    "DIRECTO":[
        "ZOOMLION HEAVY INDUSTRY PERU S.A.C.","XCMG PERU S.A.C.","AREQUIPA EXPRESO MARVISUR EIRL"
    ],
    "NO OFICIAL":[
        "SINOHYDRO CORPORATION LIMITED, SUCURSAL DEL PERU","TOP CONCRET E.I.R.L.",
        "TRACTO MOTORS SOCIEDAD ANONIMA CERRADA","BRILLANTE SL S.A.C.",
        "TMI-TYC SOCIEDAD ANONIMA CERRADA - TMI-TYC S.A.C.","VICTORIA JUAN GAS SOCIEDAD ANONIMA CERRADA",
        "EMPRESA DE SERVICIOS MULTIPLES S&M SRL.","BEIJING SHOUGANG MINE CONSTRUCTION ENGINEERING CO. LTD. SUCURSAL DEL PERU",
        "OROYA IMPORT & EXPORT S.A.C.","TERRASOLID E.I.R.L.","JUAN CARLOS & GLADYS DISTRIBUCIONES SOCIEDAD ANONIMA CERRADA",
        "PEGASUS TRANSCARGA S.A.C.","IMPORTACIONES CALAMINA J&J S.A.C.","CONCRETERA SOL DEL NORTE S.A.C.",
        "MORGILLO SELVA S.A.C.","ACUARIO H & H SOCIEDAD ANONIMA CERRADA","HAFID MOTOS S.A.C.",
        "INDUSTRIAS DEL ORIENTE TOCACHE S.A.","TRANSPORT SERVICE ERICK & GEORGE S.R.L","ORINOQUIA S.A.C.",
        "KEDA PERU BUILDING MATERIALS COMPANY SOCIEDAD COMERCIAL DE RESPONSABILIDAD LIMITADA",
        "J.C. PERUVIAN IMPORT & EXPORT S.A.C.","J & N CONTRATISTAS Y SERVICIOS SAN MIGUEL E.I.R.L.",
        "INDUSPORT ADRIANA S.A.C.","JUAN & JUAN ENVASADORA DE GAS S.A.C.",
        "GRUPO LOGISTICO AMERICANO G.L.A. SOCIEDAD ANONIMA CERRADA","INDUSTRIAS DEL TULUMAYO S.A.",
        "GRUPO MULTI MAQUINARIAS S.A.C.","COMERCIALIZADORA & CONSTRUCTORA ACEROS SOCIEDAD ANONIMA CERRADA",
        "H & E ARQUITECTURA Y PROYECTOS S.A.C.","RODTOBER E.I.R.L","OBRA Y TECNOLOGIA E.I.R.L.",
        "DRILLCOTEC PERU S.A.C.","CORPORACION Y SERVICIOS DE CHIMBOTE S.A.C","INVERSIONES ACEROS SAN MARTIN S.R.L.",
        "IMPORT EXPORT INKA LOADER EMPRESA INDIVIDUAL DE RESPONSABILIDAD LIMITADA","TRANSGRUAS PERU S.A.",
        "OSLO SOCIEDAD ANONIMA - OSLO S.A.","TRANSPORTES Y SERVICIOS MULTIPLES HUANCARUMI SOCIEDAD LIMITADA DE RESPONSABILIDAD LIMITADA",
        "PALTARUMI SOCIEDAD ANONIMA CERRADA - PALTARUMI S.A.C.","GEOEXPLORASONDEOS E.I.R.L.","DISTRIBUIDORA N & T S.A.C.",
        "CORPORATION WITHMORY S.R.L.",
    ],
    "OFICIAL":[
        "PREMIER MOTORS S.A.","CAMIONES CHINOS PERU S.A.C.","CORIEX DS S.A.C.","J.CH.COMERCIAL S.A.","ANDES MOTOR PERU S.A.C.","COMINKA MOTORS S.A.C.","ZAPLER S.A.C.","SINOTRUK PERU S.A.C."
    ],
}

IMPORTADOR_TIPO = {}
for tipo, lista in IMPORTADORES_SINOTRUK.items():
    for nombre in lista: IMPORTADOR_TIPO[nombre.upper().strip()] = tipo

def normalizar_submarca_sinotruk(marca):
    if pd.isna(marca): return None
    marca_upper = str(marca).upper().strip()
    for key, value in SINOTRUK_SUBMARCAS.items():
        if key in marca_upper:
            return value
    return None

def clasificar_importador_sinotruk(importador):
    if pd.isna(importador): return None
    return IMPORTADOR_TIPO.get(str(importador).upper().strip(), None)

# ====================================================================
# ========== MARCAS (COMPLETAS ACTUALIZADAS) ==========
# ====================================================================
BRANDS = [
    "MERCEDES BENZ","MERCEDES-BENZ","MERCEDES","FREIGHTLINER","INTERNATIONAL",
    "VOLKSWAGEN","DONGFENG","SINOTRUK","SHACMAN","KENWORTH","MITSUBISHI",
    "HYUNDAI","ISUZU","SCANIA","VOLVO","IVECO","FOTON","HOWO","DAYUN",
    "CHANGAN","MAXUS","HINO","FUSO","FAW","JAC","JMC","JBC","MAN",
    "KIA","DAF","UD","TATA","DFAC","DFSK","CAMC","BEIBEN","JOYLONG",
    "SITRAK","SINOTRUCK","HOWO MAX","TERBERG",
    "THWAITES","FIORI","BENFORD","OPAI","SANY","TEREX",
    "LIEBHERR","TONLY","CATERPILLAR","SHOUGANG",
    "XCMG","ZOOMLION","TATA DAEWOO","NORMET","KOBELCO",
    "DEMAG","BYD","PPM","TYCROP","NAFFCO","ROSENBAUER","SEAGRAVE","IVECO MAGIRUS","PEMFAB",
    "GREENLINE","GUDÃO ANDES","SHILI","JINWANG","LIANKE","SINMAN","HUANSHENG","BI","HELEX",
    "ENERGY JAST","SAIGE","CP PEREYRA","WOOPE","MEI","IRON","HOMAN","PUTZMEISTER","BARREDERA","FORLAND",
    "DAVEST","MACK","WANGPAI","QINGLING","JIANGHUAI","KOMATSU","TADANO","SANDVIK","ATLAS COPCO",
    "UTILITY","JEREH","PETRO KH","PARTINDUS","DIECI","TERRAMAC","WESTWELL","SPARTAN",
    "TOYOTA","NISSAN","FORD","SUBARU","RENAULT","TESLA","DAEWOO","NISSAN DIESEL","PEGASO",
    "LUNA","NOV ROLLIGON","PEERLESS","SUPER-ABOVE","NUESON","KEYU","BARFORD","GROVE",
    "ASTRA","KAMAZ","CHENGLONG",
    "T-KING","IVECO ASTRA","CLAVE 7","TORQ-E","HIGER","LGMG","AIMIX","CIFA",
    "FEICHI","DA YI´AN","SQMG","DRIVARO","E-ONE","POWERBOSS","HONGYUAN",
    "SHENHE LIANDA","FMAN","RAM WILLIAMS","KING LONG","JIANGHUAI","KALMAR",
    "SHAOLIN","CLD","JINSHI",
    # ===== NUEVAS MARCAS DETECTADAS =====
    "SHIFENG",
    "KAMA",
    "QIJING",
    "JIN WANG",
]
BRAND_RE = re.compile(r"\b(" + "|".join(re.escape(b) for b in BRANDS) + r")\b", re.I)
MARCAS_COMO_CARROCERIA = set(b.upper() for b in BRANDS)

# ====================================================================
# ========== CARROCERÍA ==========
# ====================================================================
CARROCERIA_MAP = {
    "REMOLCADOR":"TRACTOCAMIÓN","TRACTOR":"TRACTOCAMIÓN","TRACTO":"TRACTOCAMIÓN",
    "TRACTOCAMION":"TRACTOCAMIÓN","TRACTOCAMIÓN":"TRACTOCAMIÓN","CABEZAL":"TRACTOCAMIÓN",
    "TRACTOREMOLCADOR":"TRACTOCAMIÓN","VOLQUETE":"VOLQUETE","VOLQUETA":"VOLQUETE",
    "TOLVA":"VOLQUETE","VOLQUETE DOBLE":"VOLQUETE","DUMPER":"VOLQUETE",
    "FURGON":"FURGÓN","FURGÓN":"FURGÓN","FURGON CARGA":"FURGÓN",
    "BARANDA":"BARANDA","BARANDA FIJA":"BARANDA","BARANDA ABATIBLE":"BARANDA",
    "PLATAFORMA":"PLATAFORMA","PLANCHA":"PLATAFORMA","CISTERNA":"CISTERNA","TANQUE":"CISTERNA",
    "CAJA":"CAJA","CAJON":"CAJA","CAJÓN":"CAJA","ESTACA":"ESTACAS","ESTACAS":"ESTACAS",
    "REFRIGERAD":"REFRIGERADO","ISOTERM":"ISOTERMICO","FRIGORIFIC":"FRIGORÍFICO",
    "GANADERA":"GANADERA","PORTACONTENEDOR":"PORTACONTENEDOR","GRUA":"GRÚA","GRÚA":"GRÚA",
    "HORMIGONERA":"HORMIGONERA","MEZCLADOR":"MEZCLADORA","COMPACTADOR":"COMPACTADOR",
    "CHASIS CABINA":"CHASIS CABINA","CAMA BAJA":"CAMA BAJA",
    "PANEL":"FURGÓN",
    "MINI DUMPER":"VOLQUETE",
    "PICK UP":"PLATAFORMA",
    "BOMBERO":"CARRO BOMBA",
    "PERFORADOR":"MAQUINARIA",
    "ELEVADOR":"PLATAFORMA ELEVADORA",
    "REPARAVIAS":"MAQUINARIA",
    "RADIOLOGICO":"MAQUINARIA",
    "EXPLOSIVOS":"MAQUINARIA",
    "AUXILIO MECANICO":"GRÚA",
}

# ====================================================================
# ========== MODELOS POR MARCA (ACTUALIZADO CON NUEVAS MARCAS) ==========
# ====================================================================
MODELOS_POR_MARCA = {
    "FREIGHTLINER":["M2","M2 106","M2 112","CASCADIA","COLUMBIA","CENTURY","FL112","BUSINESS CLASS"],
    "INTERNATIONAL":["4300","4400","4700","4900","7600","WORKSTAR","DURASTAR","LONESTAR","PROSTAR","HV607"],
    "KENWORTH":["T370","T440","T660","T680","T800","W900","K270","K370"],
    "MERCEDES BENZ":["ATEGO","ACTROS","AXOR","SPRINTER","AROCS","AROCS 3342","AROCS 4848K","NEW ACTROS","ZETROS","L 1620","L 1632","L 2632","ACCELO","OF 1730","1520/48","LO 916/48","OF 1721/59","1828 R"],
    "MERCEDES-BENZ":["ATEGO","ACTROS","AXOR","SPRINTER","AROCS","AROCS 3342","AROCS 4848K","NEW ACTROS","ZETROS","L 1620","L 1632","L 2632","ACCELO","OF 1730","1520/48","LO 916/48","OF 1721/59","1828 R"],
    "VOLKSWAGEN":["CONSTELLATION","DELIVERY","WORKER","24.280","31.280"],
    "SCANIA":["G410","G440","G450","R440","R450","R500","P410","P440","G500","G540","G550","R410","R460","R540","R550","R620","P420","P450","P460","G360","G410 A6X4","R500 A6X4","P410 B6X4","P450 B8X4","G540 B8X4","R620 B10X4"],
    "VOLVO":["FH","FM","FMX","VM","VNL","VNR","VHD","FMX 6X4R","FMX 8X4R","FMX11 6X4R","VMX 6X4 R","FH 6X4 T","FM 6X4 T","FMX 6X4 R","FMX 8X4 R","FM350"],
    "HYUNDAI":["HD78","HD120","HD170","HD260","HD270","XCIENT","HD35","HD65","HD10","H100 TRUCK","EX6","HQC2"],
    "HINO":["300","500","700","DUTRO","RANGER","XZU720L"],
    "FUSO":["CANTER","FIGHTER","SUPER GREAT"],
    "ISUZU":["NPR","NQR","FRR","FTR","FVR","GIGA","NQR90L-MQ5VAYPEN","NPR75L-KL5VAYPEN","NPS75L-HJ5VAYPEN","XZU720L","600 P","KV100 BUS"],
    "SITRAK":["C7H","C9H","ZZ4256V324HE1B","ZZ4256V384HE1C","ZZ4256V384HE1CB","ZZ4257V384HE1C","ZZ4257V424KE1CK","ZZ4257V344JB1R","ZZ1316N306GE1","ZZ4252V3247F1W","ZZ4256V344HE1B","ZZ4256V364HE1B","ZZ4256V384HE1L","ZZ1256N364MD1","ZZ5226N481GF1","ZZ5336N464GF1","ZZ5446V406ME1","ZZ1256V564ME1","ZZ3256N364SE1","ZZ3256V364HE1","ZZ1316N306ME1"],
    "SINOTRUK":["C7H","T7H","MAX","MAX-E","ZZ4257V344HE1","ZZ4257V344HB1","ZZ4257V384HE1C","ZZ5237N521GE1","ZZ1315N3063E1","ZZ1257V384GB1","ZZ1317N306GF1","TX 350","ZZ1317N466JE1","ZZ3257V364GB1","ZZ3257V364GC1","ZZ1317V466JE1","ZZ1257V5847E1","ZZ1257V5847F1","ZZ1167N561GC1","ZZ5447TXFV466MF1","ZZ1148F3415E1C","ZZ3317V286GC1","ZZ3257N3647P1","ZZ3168F3415E1","ZZ1167M561GE1"],
    "SHACMAN":["X3000","X5000","X6000","F3000","M3000","L3000","LT625","SX42585Y344C","SX42584V404T","SX4250XC4Q2","SX42586W404C","SX5166ZYSMM381C","SX5318JSQ6W456C","SX5258GJB6S384C","SX5258GJB6R364C","SX5258GJB6R384C","SX5310GJBMB6","SX5318JSQ6W366C","SX5318JSQ62386C","SX5258ZYSHT564T","SX325862354C","SX331862306C","SX3255M3M39","SX331852306C"],
    "FOTON":["AUMAN","AUMARK","VIEW","EST","BJ4269","BJ4253","BJ1226","BJ4353","BJ5319GJB-AF","BJ4259SMFKB","BJ4269SNFKB","BJ3259DLPKB"],
    "FAW":["J5M","J6P","CA4250","CA4163","CA4163P1K2E5A80"],
    "THWAITES":["SKT105S","TA6","C06","D11","C05","C06 PRO"],
    "CAMC":["AH5316GJB6L6","HN5250P35C6M3","HN5250P35C6M3GJB","HN1310HB35CLM5J"],
    "IVECO":["TRAKKER","S-WAY","T-WAY","X-WAY","TECTOR","EUROCARGO","DAILY","AS440X46T/P","AD410T50H","380T41H","BA3C"],
    "DONGFENG":["CAPTAIN","KINGRUN","DFH4250C2","DFH4180C80","DFH3250A","DFH3310A6","DFL1250AW2","DFV4258GP6C","DFH4271","YZR5070TQZEQ","DOLLICAR D6","DFH3250A1"],
    "MAN":["TGS","TGX","TGM","TGL","TGS 26.480","TGS 40.480","TGS 41.480","TGX 26.540"],
    "DAF":["XF530","CF410","CF480","XF105","CF85","XF530 FTM"],
    "JAC":["SUNRAY","X200","HFC4252","HFC4255","HFC3251KN","HFC3251P1K5E39V"],
    "SANY":["SYZ316C-8S","SYM3312ZZX1E","EVJL350HG64-80","HQC42503S1S12E","SKT105S","SYG5180THB","SAC2500E","STC500C5"],
    "XCMG":["NXG4250D5NC","NXG4250D5WC","XGA3250D5WC","XGA3251D5WC","XGA3312D5WE","NXG3250D5NC","QY25K5D"],
    "ASTRA":["HD9","HD9 64.41","HD9 64.44T","HD9 64.48","HD9 84.52"],
    "DAYUN":["CGC4250","CGC4251"],
    "CHENGLONG":["LZ4250H7DM03"],
    "KAMAZ":["KAMAZ 6520","6520"],
    "MACK":["ANTHEM","GRANITE","PINNACLE","VISION","MR688S"],
    "HOMAN":["ZZ1048D3314D145","ZZ1148F3415E1C"],
    "SINMAN":["ZL-05","ZL100","ZL150","ZL200","ZL300","ZL50-2","ZL50-3","ZL50-5","ZL50-6","ZWY-40"],
    "GREENLINE":["FB130","H21-180","TC1-110","TC1-130","TC1-160","TC1-160C","TC1-85","TC2-110A","TC2-130","TC2-160"],
    "BI":["BI-4T","BI08E","BI100","BI150","BI150D","BI150E","BI200","BI250E","BI250ERA","BI270D","BI300D","BI350D","BI400D"],
    "HELEX":["NR-D15","NR-D25","NR-D30","NR-E10","NR-E15","NR-E15L","NR-E30","NR-HP6","NR-T60","NR-TE60"],
    "ENERGY JAST":["CRG13","CRG13T","CRG15","CRG16T"],
    "SAIGE":["CHUANQI","CHUANQI PLUS","JS","Q13","ST"],
    "WOOPE":["T-1000","T-3000"],
    "CP PEREYRA":["CP 135","CP136","EU-156T","HS155","HS160","SL-153T"],
    "MEI":["MEI 4219","MEI 50H","MEI24MZ","72V1200W"],
    "DAVEST":["E-CARGO","E-CARGO-2","E-CARGO-3"],
    "IRON":["FENGCHI"],
    "QOMOLO":["E-TRUCK"],
    "FACAM":["NR-T60","NR-E15","NR-E20","NR-GT5","NR-TE60"],
    "LGMG":["CMS40","CMT 106","CMT106","MT96H","RTH100","RTH136"],
    "CLAVE 7":["GP6850","KMC1035D4","KMC1048P4","KMC1142P4","KMC1165P5","KMC5023XXY305S6","QL1100A8MAHY","QL1100A8PAY","QL1110ANMACY","QL1110ANPACY-PW35A"],
    "TONLY":["DTH145","TL885A","TLD96","TLH135","TLK451"],
    "T-KING":["ZB1020BDC3F","ZB1020BSC3F","ZB1032VDD2L","ZB1032VSD2L","ZB1040VDD2L","ZB1041JDD6F","ZB1041VDD2L","ZB1042LDD6F","ZB1043JDD6L","ZB1080JDE3F","ZB5020XXYBDC3F","ZB5032XXYVDD2L"],
    "HIGER":["KLQ6126DFC","KLQ6756DFE4A","KLQ6898BA","KLQ6898EBA"],
    "LK":["LK135D","LK270D"],
    "DRIVARO":["HLW5030BG","HLW5040BD"],
    "FIORI":["DB460","DBX35","DBX50"],
    "SUPER-ABOVE":["SA5070TSLD3","SA5090TQZ6","SA5250GJB5","SA5251GJB","SA5251GPS","SA5252TQZS5","SA5253ZYS","SA5254ZYS5"],
    "E-ONE":["ARFF TITAN P801","RESCUE TYPHOON"],
    "FMAN":["FM540SLA PLUS","HN5250P35C6M5GJB"],
    "AIMIX":["AS-3.5","AS-3.5C","AS-4.0"],
    "IVECO ASTRA":["HD9 64.41","HD9 64.48","HD9 64.48T","HD9 84.52"],
    "TORQ-E":["JX 002","VOLQ 2.0"],
    "CIFA":["COGUARO 4 3A"],
    "FEICHI":["SDC-2350D"],
    "DA YI´AN":[],
    "SQMG":["JBC-4.0D"],
    "POWERBOSS":["10XT3DSL","SW6XKLPG"],
    "HONGYUAN":["HY500","HY550"],
    "SHENHE LIANDA":["ESH5180TBC","ESH5250GJB","ESH5310GGJB"],
    "RAM WILLIAMS":["2500 4X4 RANGER"],
    "KING LONG":["XMQ6520EV"],
    "JIANGHUAI":["JHH1200DZH-30C"],
    "KALMAR":["TR618I"],
    "SHAOLIN":["SL6120W5VAT"],
    "CLD":["CLD5030XLC6TH"],
    "JINSHI":["KFC-18"],
    "C&C":["QCC4253N664"],
    "RLQ":["RLQ5180GSJJF6"],
    "BENFORD TEREX":["PT6000","PT9000"],
    "BEIJING FOTON DAIMLER AUT":["BJ1181Y6AKL-01"],
    "ISUZU QINGLING":["600 P","KV100 BUS"],
    "RCM":["BOXER D PLUS.1","BOXER SK2 PLUS.1","R DUEMILA E/1"],
    "GDC-02":["7YP-1450DAB1"],
    "SHANDONG JULONG":["1.7*2.4"],
    "SHANDONG JIESHENG":["JS-300"],
    "ZHENGZHOU LIANKE MACHINERY":["MW3P"],
    "HAMAC":["HMC400"],
    "ZNA - ZHENGZHOU NISSAN AUTOMOBILE":["RICH 7 EV"],
    "AUMAN":["BJ5313GJB-AA","BJ5253Y6DLL-01","BJ5313GJB-LM","BJ5319GJB-AD","BJ5319GJBY6GRL-01","BJ4259Y6DHL-25"],
    "HOWO MAX":["ZZ4257V424KF1LK"],
    "WANGPAI":["CDW5180GJBA2Q6"],
    "OPAI":["L2E-U"],
    "JIV":["KMC1035D4","KMC1040D3","KMC1067D4"],
    # ===== NUEVOS MODELOS PARA NUEVAS MARCAS =====
    "SHIFENG":["SSF3042DDP84","SSF3042DDP85"],
    "KAMA":["KMC1067P4","KMC5067XXYD4","KMC1165D5","KMC5165XXYD5","KMC5167XXYP5"],
    "QIJING":["QHV5180JSQDF"],
    "JIN WANG":["UK-6"],
}

MODEL_PATTERNS = [
    r'\b(M2\s*106|M2\s*112|CASCADIA|COLUMBIA|CENTURY)\b',
    r'\b(4300|4400|4700|4900|7600|WORKSTAR|DURASTAR|LONESTAR|PROSTAR|HV607)\b',
    r'\b(T370|T440|T660|T680|T800|W900|K270|K370)\b',
    r'\b(ATEGO|ACTROS|AXOR|SPRINTER|AROCS|ZETROS|ACCELO|L\s*1620|L\s*1632|L\s*2632|OF\s*1730|1520/48|LO\s*916|OF\s*1721|1828\s*R)\b',
    r'\b(CONSTELLATION|DELIVERY|WORKER|24\.280|31\.280)\b',
    r'\b(G\d{3}|R\d{3}|P\d{3})\b',
    r'\b(FH|FM|FMX|VM|VNL|VNR|VHD|FM350)\b',
    r'\b(HD\d{2,3}|XCIENT|H100\s*TRUCK|EX6|HQC2)\b',
    r'\b(DUTRO|RANGER|[35]00|XZU720L)\b',
    r'\b(CANTER|FIGHTER|SUPER\s*GREAT)\b',
    r'\b(NPR|NQR|FRR|FTR|FVR|GIGA|NPS)\b',
    r'\b(C7H|C9H|T7H|MAX-E|MAX\s*E)\b',
    r'\b(X[35]000|F3000|M3000|L3000|LT\d{3,4})\b',
    r'\b(AUMAN|AUMARK|VIEW|J[56][MP]|CA\d{4})\b',
    r'\b(SKT\d{3}|TA\d|C0[56]|D11|C06\s*PRO)\b',
    r'\b(ZZ\d{4}[A-Z]\d{4}[A-Z0-9]{2,4})\b',
    r'\b(TL\d{3}|RH\d{3})\b',
    r'\b(DB\d{3})\b',
    r'\b(TMS\d{3})\b',
    r'\b(SX\d{4}[A-Z0-9]{4,8})\b',
    r'\b(HN\d{4}[A-Z0-9]{4,8})\b',
    r'\b(BJ\d{4}[A-Z0-9-]{4,8})\b',
    r'\b(DFL\d{4}|DFH\d{4}|DFV\d{4})\b',
    r'\b(K2500|STARIA|PARTNER|BERLINGO|GH8JP7A|XG110|ZK6760|TANKE\s*350P)\b',
    r'\b(FJ|FA|FM350|FMX\s*[68]X4)\b',
    r'\b(GDC-?2\.?5T|DP-?2\.?5T)\b',
    r'\b(TRAKKER|S-WAY|T-WAY|X-WAY|TECTOR|EUROCARGO|DAILY)\b',
    r'\b(CAPTAIN|KINGRUN)\b',
    r'\b(TGS|TGX|TGM|TGL)\b',
    r'\b(XF\d{3}|CF\d{3})\b',
    r'\b(SUNRAY|X200)\b',
    r'\b(NXG\d{4}|XGA\d{4}|QY\d{2})\b',
    r'\b(HD9|CGC\d{4})\b',
    r'\b(LZ\d{4})\b',
    r'\b(KAMAZ|6520)\b',
    r'\b(ANTHEM|GRANITE|PINNACLE|VISION|MR\d{3})\b',
    r'\b(CDW5180GJBA2Q6)\b',
    r'\b(HLW5030BG|HLW5040BD)\b',
    r'\b(CLD5030XLC6TH)\b',
    r'\b(KFC-18)\b',
    r'\b(COGUARO 4 3A)\b',
    r'\b(HMC400)\b',
    r'\b(SSF3042DDP84|SSF3042DDP85)\b',
    r'\b(KMC1067P4|KMC5067XXYD4|KMC1165D5|KMC5165XXYD5|KMC5167XXYP5)\b',
    r'\b(QHV5180JSQDF)\b',
    r'\b(UK-6)\b',
]

MODEL_RE = re.compile('|'.join(MODEL_PATTERNS), re.IGNORECASE)
VOLQUETE_RE = re.compile(r'\b(VOLQUETE|VOLQUETA|TOLVA|VOLQUETE\s*DOUBLE|DUMPER)\b', re.IGNORECASE)
GENERIC_CODE_RE = re.compile(r"(?:^|[,;\s])((?:CH/VIN)|[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9.]{0,14})\s*:",)
CATEGORY_RE = re.compile(r"^\s*(N\d)", re.IGNORECASE)
YEAR_RE = re.compile(r"A[ÑN]O(?:\s*MOD)?\s*:?\s*((?:19|20)\d{2})", re.IGNORECASE)
NUM_RE = re.compile(r"-?\d+(?:[.,]\d+)?")
FUEL_RE = re.compile(r"DIESEL|PETROLEO|GASOLINA|GAS\b|GNV|GLP|ELECTR|H[IÍ]BRID|DUAL|BIODIESEL", re.I)

# ====================================================================
# ========== FUNCIONES ==========
# ====================================================================

def clasificar_peso(kg_bruto):
    if pd.isna(kg_bruto) or kg_bruto is None: return None
    kg = float(kg_bruto)
    for c,(mn,mx) in PESO_CATEGORIAS.items():
        if mn<=kg<=mx: return c
    return "LIGERO (<3.5T)" if kg<3500 else None

def es_volquete_pesado(row):
    if pd.isna(row.get('carroceria')) or pd.isna(row.get('kg_bruto')): return "NO"
    return "SÍ" if 'VOLQUETE' in str(row['carroceria']).upper() and float(row['kg_bruto'])>=VOLQUETE_PESADO_MIN_KG else "NO"

# ============================================================
# ✅ CLASIFICACIÓN WITHMORY
# ============================================================
def clasificar_withmory(row):
    """
    Clasifica según la lógica WITHMORY:
    - TRACTOCAMIÓN: si carroceria contiene TRACTOCAMIÓN, REMOLCADOR o TRACTOR
    - VOLQUETE: si carroceria contiene VOLQUETE (todos, sin importar peso)
    - CATEGORIA_PESO: si no entra en las anteriores
    """
    carroceria = str(row.get('carroceria', '')).upper()
    kg_bruto = row.get('kg_bruto', 0)
    categoria_peso = row.get('categoria_peso', '')
    
    # 1. TRACTOCAMIÓN
    if any(x in carroceria for x in ['TRACTOCAMIÓN', 'TRACTOCAMION', 'REMOLCADOR', 'TRACTOR']):
        return 'TRACTOCAMIÓN'
    
    # 2. VOLQUETE (todos los volquetes, sin importar peso)
    if 'VOLQUETE' in carroceria or 'VOLQUETA' in carroceria:
        return 'VOLQUETE'
    
    # 3. Si no es tracto ni volquete, usar categoria_peso
    if pd.notna(categoria_peso) and str(categoria_peso).strip():
        return str(categoria_peso).strip()
    
    return 'SIN_CATEGORIA'

# ============================================================
# ✅ CORREGIDO: FILTRO DE CARROCERÍA - SOLO EXCLUYE MOTOS Y L5/L6
# ============================================================
def es_carroceria_excluida(row):
    """
    EXCLUYE SOLAMENTE:
    - Motos, trimotos, cuatrimotos, motocares
    - Vehículos L5, L6 (subterráneos, mini dumpers, vehículos ligeros)
    
    MANTIENE:
    - TODOS los volquetes (pesados, livianos, mineros)
    - TODOS los camiones (N2, N3)
    - TODOS los vehículos comerciales
    """
    if isinstance(row, dict) or hasattr(row, 'get'):
        carroceria = row.get('carroceria')
        kg_bruto = row.get('kg_bruto')
        categoria = row.get('categoria', '')
        descripcion = row.get('_descripcion', '')
        marca = row.get('marca', '')
    else:
        carroceria = row
        kg_bruto = None
        categoria = ''
        descripcion = ''
        marca = ''
    
    if pd.isna(carroceria):
        return False
    
    cu = str(carroceria).upper()
    cat = str(categoria).upper()
    desc = str(descripcion).upper()
    mar = str(marca).upper()
    
    # ============================================================
    # 1. NUNCA EXCLUIR VOLQUETES (pase lo que pase)
    # ============================================================
    if 'VOLQUETE' in cu or 'VOLQUETA' in cu:
        return False  # Siempre mantener
    
    # ============================================================
    # 2. MANTENER VOLQUETES DE MARCAS DE MAQUINARIA PESADA
    # ============================================================
    marcas_volquete = ['SANY', 'XCMG', 'KOMATSU', 'TONLY', 'ZOOMLION', 'LGMG', 'LIUGONG', 'SHACMAN']
    if any(m in mar for m in marcas_volquete) and ('VOLQUETE' in cu or 'DUMPER' in cu):
        return False  # Mantener
    
    # ============================================================
    # 3. EXCLUIR VEHÍCULOS L5 Y L6 (subterráneos, livianos, mini dumpers)
    # ============================================================
    if cat.startswith('L5') or cat.startswith('L6'):
        return True  # Excluir
    
    # ============================================================
    # 4. EXCLUIR MOTOS, TRIMOTOS, CUATRIMOTOS, MOTOCARES
    # ============================================================
    if any(x in cu for x in ['MOTO', 'TRIMOTO', 'CUATRIMOTO', 'MOTOCAR', 'MOTOTAXI']):
        return True
    
    # ============================================================
    # 5. EXCLUIR CARROCERÍAS NO DESEADAS (de la lista)
    # ============================================================
    return any(e in cu for e in CARROCERIAS_EXCLUIR)

def es_estado_nuevo(e):
    if pd.isna(e): return False
    eu = str(e).upper().strip()
    return any(n in eu for n in ESTADOS_NUEVOS)

def es_km_nuevo(k):
    if pd.isna(k) or k is None: return True
    try: return float(k)<=KM_MAX_NUEVO
    except: return True

def extraer_fecha_dua(df):
    if 'fecha_dua' not in df.columns:
        df['año_dua']=df['mes_dua']=df['trimestre_dua']=None; return df
    f = pd.to_datetime(df['fecha_dua'], errors='coerce')
    df['año_dua']=f.dt.year.astype('Int64')
    df['mes_dua']=f.dt.month.astype('Int64')
    df['trimestre_dua']=f.dt.quarter.map(TRIMESTRES)
    return df

def to_num(v):
    if pd.isna(v) or v is None: return None
    m = NUM_RE.search(str(v).replace(",","."))
    return float(m.group(0)) if m else None

def to_int(v):
    n = to_num(v)
    return int(n) if n is not None else None

def normalizar_carroceria(raw_ca):
    if pd.isna(raw_ca) or not raw_ca: return None
    ca_upper = str(raw_ca).upper().strip()
    if ca_upper in MARCAS_COMO_CARROCERIA: return None
    for k,v in CARROCERIA_MAP.items():
        if k in ca_upper: return v
    return ' '.join(w.capitalize() for w in str(raw_ca).split())

def detectar_modelo_por_texto(desc, marca=None):
    if pd.isna(desc) or not desc: return None
    m = MODEL_RE.search(str(desc))
    if m: return re.sub(r'\s+',' ',m.group(0).strip()).upper()
    if marca and not pd.isna(marca):
        mu = str(marca).upper()
        if mu in MODELOS_POR_MARCA:
            for mod in MODELOS_POR_MARCA[mu]:
                if mod.upper() in str(desc).upper(): return mod.upper()
    return None

# ====================================================================
# ========== PARSEO ==========
# ====================================================================
def parse_descripcion_vectorized(df):
    print("  Inicializando columnas extraídas...")
    for col in EXTRACTED_ORDER: df[col] = None
    df = extraer_fecha_dua(df)
    mask = df['_descripcion'].notna()
    if not mask.any(): return df
    descs = df.loc[mask,'_descripcion'].astype(str)
    print(f"  Procesando {mask.sum()} descripciones...")
    
    print("  Categorizando por peso bruto...")
    if 'kg_bruto' in df.columns: df['categoria_peso'] = df['kg_bruto'].apply(clasificar_peso)
    
    df.loc[mask,'categoria'] = descs.str.extract(CATEGORY_RE, expand=False).str.upper()
    df.loc[mask,'marca'] = descs.str.extract(BRAND_RE, expand=False).str.upper()
    df.loc[mask,'anio_modelo'] = pd.to_numeric(descs.str.extract(YEAR_RE, expand=False), errors='coerce').astype('Int64')
    df.loc[mask,'color'] = descs.str.extract(r'C1\s*:\s*([^,;]+)', expand=False)
    df.loc[mask,'combustible'] = descs.str.extract(r'CO\s*:\s*([^,;]+)', expand=False)
    df.loc[mask,'largo_mm'] = pd.to_numeric(descs.str.extract(r'LA\s*:\s*([^,;]+)', expand=False), errors='coerce')
    df.loc[mask,'ancho_mm'] = pd.to_numeric(descs.str.extract(r'AN\s*:\s*([^,;]+)', expand=False), errors='coerce')
    df.loc[mask,'alto_mm'] = pd.to_numeric(descs.str.extract(r'AL\s*:\s*([^,;]+)', expand=False), errors='coerce')
    
    df.loc[mask,'carroceria'] = descs.str.extract(r'CA\s*:\s*([^,;]+)', expand=False).apply(normalizar_carroceria)
    
    print("  Detectando modelos...")
    df.loc[mask,'modelo'] = descs.str.extract(r'MODELO\s*:\s*([^,;]+)', expand=False)
    msm = mask & df['modelo'].isna()
    if msm.any(): df.loc[msm,'modelo'] = df.loc[msm].apply(lambda r: detectar_modelo_por_texto(r['_descripcion'], r.get('marca')), axis=1)
    
    print("  Normalizando submarcas SINOTRUK...")
    df['submarca_sinotruk'] = df['marca'].apply(normalizar_submarca_sinotruk)
    if 'importador' in df.columns: df['tipo_importador_sinotruk'] = df['importador'].apply(clasificar_importador_sinotruk)
    
    print("  Detectando carrocería por palabras...")
    msc = mask & df['carroceria'].isna()
    if msc.any(): df.loc[msc,'carroceria'] = df.loc[msc,'_descripcion'].astype(str).apply(lambda d: 'VOLQUETE' if VOLQUETE_RE.search(str(d)) else None)
    msc2 = mask & df['carroceria'].isna()
    if msc2.any(): df.loc[msc2,'carroceria'] = df.loc[msc2,'_descripcion'].astype(str).str.upper().apply(lambda d: 'TRACTOCAMIÓN' if 'REMOLCADOR' in d or 'TRACTOR' in d else None)
    
    mm = df['carroceria'].notna()
    if mm.any(): df.loc[mm,'carroceria'] = df.loc[mm,'carroceria'].apply(lambda x: None if str(x).upper().strip() in MARCAS_COMO_CARROCERIA else x)
    
    print("  Identificando volquetes pesados (>25 Ton)...")
    df['es_volquete_pesado'] = df.apply(es_volquete_pesado, axis=1)
    
    # ============================================================
    # ✅ CORRECCIÓN: TRACTOCAMIONES CON CARGA ÚTIL = 0
    # ============================================================
    print("  Corrigiendo carga útil para tractocamiones...")
    if 'carroceria' in df.columns and 'carga_util' in df.columns:
        tracto_mask = df['carroceria'].str.upper().str.contains('TRACTOCAMI|TRACTOR|REMOLCADOR', na=False)
        if tracto_mask.any():
            df.loc[tracto_mask, 'carga_util'] = 0
            print(f"    ✅ Carga útil corregida a 0 para {tracto_mask.sum()} tractocamiones")
    
    # ============================================================
    # ✅ CLASIFICACIÓN AUTOMÁTICA
    # ============================================================
    print("  Clasificando vehículos...")
    
    if 'categoria' in df.columns:
        df['clasificacion'] = df['categoria']
    elif 'kg_bruto' in df.columns:
        def clasificar_por_peso(kg):
            if pd.isna(kg):
                return 'SIN_CLASIFICAR'
            try:
                kg = float(kg)
                if kg < 3500:
                    return 'LIGERO'
                elif kg < 6000:
                    return 'LDT 1'
                elif kg < 10000:
                    return 'LDT 2'
                elif kg < 15000:
                    return 'MDT 1'
                elif kg < 17000:
                    return 'MDT 2'
                elif kg < 25000:
                    return 'MDT 3'
                elif kg < 33000:
                    return 'SEMI PESADO'
                else:
                    return 'PESADO'
            except (ValueError, TypeError):
                return 'SIN_CLASIFICAR'
        df['clasificacion'] = df['kg_bruto'].apply(clasificar_por_peso)
    else:
        df['clasificacion'] = 'SIN_CLASIFICAR'
    
    if 'transmision' in df.columns:
        df['caja'] = df['transmision']
    else:
        df['caja'] = 'SIN_DATO'
    
    df['modelo_flag'] = 'ok'
    
    print(f"    ✅ Clasificación: {df['clasificacion'].notna().sum()} registros")
    print(f"    ✅ Caja: {df['caja'].notna().sum()} registros")
    print(f"    ✅ modelo_flag: ok para todos")
    
    print("  Parseando códigos adicionales...")
    def parse_row(desc):
        if pd.isna(desc): return {}
        s = str(desc).strip()
        result = {}
        matches = list(GENERIC_CODE_RE.finditer(s))
        for i,m in enumerate(matches):
            code = m.group(1).upper()
            if code not in CODES and code != "CH/VIN": continue
            vs, ve = m.end(), matches[i+1].start(1) if i+1<len(matches) else len(s)
            raw = s[vs:ve].strip().strip(",;").strip()
            if not raw: continue
            if code == "CH/VIN": result.setdefault("chasis",raw); result.setdefault("vin",raw)
            elif code == "CO":
                if FUEL_RE.search(raw): result.setdefault("combustible",raw)
                else: result.setdefault("color",raw)
            elif code in ["CA","C1","LA","AN","AL","MODELO"]: pass
            else:
                col, typ = CODES[code]
                if col in result: continue
                if typ=="int": result[col]=to_int(raw)
                elif typ=="num": result[col]=to_num(raw)
                elif typ=="power": result[col]=raw; result["potencia_hp"]=to_num(raw.split("@")[0])
                else: result[col]=raw
        return result
    parsed = descs.apply(parse_row)
    for col in EXTRACTED_ORDER:
        if col in ['año_dua','mes_dua','trimestre_dua','categoria','categoria_peso','marca','submarca_sinotruk','modelo','anio_modelo','carroceria','es_volquete_pesado','tipo_importador_sinotruk','color','combustible','largo_mm','ancho_mm','alto_mm']: continue
        df.loc[mask,col] = parsed.apply(lambda x: x.get(col))
    return df

# ====================================================================
# ========== PROCESAMIENTO ==========
# ====================================================================
def process_file(src, out):
    print(f"\n{'='*60}\n  {src.name}\n{'='*60}")
    print("  Leyendo archivo con pandas...")
    try: df = pd.read_excel(src, header=HEADER_ROW-1)
    except Exception as e: print(f"  ERROR: {e}", file=sys.stderr); return False
    if df.empty: print("  Sin datos."); return False
    total_original = len(df)
    df = df.rename(columns={k:v for k,v in HARD_COLS.items() if k in df.columns})
    if '_descripcion' not in df.columns: print("  ERROR: 'Descripcion Comercial' no encontrada"); return False
    df = parse_descripcion_vectorized(df)
    
    print(f"\n  {'='*50}\n  APLICANDO FILTROS\n  {'='*50}")
    print(f"  Registros originales: {total_original}")
    me = df['estado'].apply(es_estado_nuevo) if 'estado' in df.columns else pd.Series(True,index=df.index)
    mk = df['kilometraje'].apply(es_km_nuevo) if 'kilometraje' in df.columns else pd.Series(True,index=df.index)
    
    mc = df.apply(es_carroceria_excluida, axis=1)
    mc = ~mc
    
    print(f"  Excluidos por estado: {(~me).sum()}")
    print(f"  Excluidos por kilometraje: {(~mk).sum()}")
    print(f"  Excluidos por carrocería: {(~mc).sum()}")
    df_f = df[me & mk & mc].copy()
    
    print("  Eliminando duplicados de VIN/Chasis...")
    if 'vin' in df_f.columns:
        vin_dups = df_f[df_f['vin'].notna() & df_f['vin'].duplicated(keep=False)]
        if len(vin_dups) > 0:
            print(f"    {len(vin_dups)} VIN duplicados, manteniendo el primero...")
            df_f = df_f.drop_duplicates(subset=['vin'], keep='first')
        else:
            print(f"    ✅ Sin VIN duplicados")
    if 'chasis' in df_f.columns:
        chasis_dups = df_f[df_f['chasis'].notna() & df_f['chasis'].duplicated(keep=False)]
        if len(chasis_dups) > 0:
            print(f"    {len(chasis_dups)} Chasis duplicados, manteniendo el primero...")
            df_f = df_f.drop_duplicates(subset=['chasis'], keep='first')
        else:
            print(f"    ✅ Sin Chasis duplicados")
    
    # ============================================================
    # ✅ AGREGAR CATEGORÍA WITHMORY
    # ============================================================
    print("  Agregando categoría WITHMORY...")
    df_f['categoria_withmory'] = df_f.apply(clasificar_withmory, axis=1)
    
    conteo = df_f['categoria_withmory'].value_counts()
    print(f"    Categorías:")
    for cat, count in conteo.items():
        print(f"      - {cat}: {count}")
    
    tf = len(df_f)
    print(f"\n  RESULTADO FINAL: {tf} REGISTROS")
    if tf==0: return False
    
    if 'año_dua' in df_f.columns:
        print(f"\n  DISTRIBUCIÓN POR AÑO:")
        for a,c in df_f['año_dua'].value_counts().sort_index().items(): print(f"    {int(a)}: {c:>5} ({100*c/tf:.1f}%)")
    
    ms = df_f['submarca_sinotruk'].notna()
    if ms.sum()>0:
        print(f"\n  SINOTRUK: {ms.sum()} registros")
        print(f"  Submarcas:")
        for s,c in df_f.loc[ms,'submarca_sinotruk'].value_counts().items(): print(f"    {s:<25} {c:>5}")
        if 'tipo_importador_sinotruk' in df_f.columns:
            print(f"  Tipo importador:")
            for t,c in df_f.loc[ms,'tipo_importador_sinotruk'].value_counts().items(): print(f"    {t:<15} {c:>5}")
    
    tractos = df_f[df_f['carroceria']=='TRACTOCAMIÓN']
    volq = df_f[df_f['carroceria']=='VOLQUETE']
    print(f"\n  Tractocamiones: {len(tractos)} | Volquetes: {len(volq)}")
    if 'es_volquete_pesado' in df_f.columns: print(f"  Volquetes > 25 Ton: {len(df_f[df_f['es_volquete_pesado']=='SÍ'])}")
    
    rev = df_f[df_f['vin'].isna() & df_f['chasis'].isna() & df_f['marca'].isna()]
    print(f"\n  Filas a revisar: {len(rev)}")
    
    print("\n  Escribiendo resultado...")
    hard_out = [v for k,v in HARD_COLS.items() if v!="_descripcion"]
    columns = [c for c in hard_out+EXTRACTED_ORDER if c in df_f.columns]
    if '_descripcion' in df_f.columns and '_descripcion' not in columns: columns.append('_descripcion')
    out.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active; ws.title="estructurado"
    dfo = df_f[columns].copy()
    for col in dfo.columns:
        if dfo[col].dtype=='Int64': dfo[col]=dfo[col].astype(object)
        elif dfo[col].dtype=='object': dfo[col]=dfo[col].where(dfo[col].notna(),None)
    for r in dataframe_to_rows(dfo, index=False, header=True): ws.append(r)
    if not rev.empty:
        ws2=wb.create_sheet("_revisar")
        rc=['dua_dam','estado','kg_bruto','categoria_peso','carroceria','marca','submarca_sinotruk','modelo','tipo_importador_sinotruk','_descripcion','categoria_withmory']
        for r in dataframe_to_rows(rev[[c for c in rc if c in rev.columns]], index=False, header=True): ws2.append(r)
    wb.save(out)
    print(f"  Escrito: {out}  ({tf} registros, {len(columns)} columnas)")
    return True

# ====================================================================
# ========== MAIN ==========
# ====================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs-dir", default=INPUTS_DIR)
    ap.add_argument("--outputs-dir", default=OUTPUTS_DIR)
    ap.add_argument("--input")
    args = ap.parse_args()
    srcs = [Path(args.input)] if args.input else sorted(Path(args.inputs_dir).glob("*.xlsx"))
    if not srcs: print("No .xlsx"); return 1
    out_dir = Path(args.outputs_dir); ok = 0
    for src in srcs:
        if not src.exists(): continue
        if process_file(src, out_dir/f"{src.stem}_estructurado.xlsx"): ok+=1
    print(f"\n{'='*60}\n  Listo: {ok}/{len(srcs)} archivos.\n{'='*60}")
    return 0 if ok else 1

if __name__=="__main__": raise SystemExit(main())