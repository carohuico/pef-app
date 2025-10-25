def extraer_indicadores(file_path):
    #leer txt desde archivo
    with open(file_path, 'r', encoding='utf-8') as f:
        data = f.read()
    #valores a extraer = Clase, Confianza, x_min, y_min, x_max, y_max
    indicadores = []
    lines = data.split('\n')
    start_extracting = False
    for line in lines:
        if 'Detecciones:' in line:
            start_extracting = True
            continue
        if start_extracting:
            if '------' in line or line.strip() == '':
                continue
            parts = line.split()
            if len(parts) >= 6:
                clase = parts[0]
                # intentar convertir confianza a float; hay casos donde la línea es
                # el encabezado "Clase Confianza x_min ..." o contiene texto no numérico.
                raw_conf = parts[1]
                # limpiar porcentajes y comas decimales
                raw_conf_clean = raw_conf.strip().rstrip('%').replace(',', '.')
                try:
                    confianza = float(raw_conf_clean)
                except Exception:
                    # no es un valor numérico (probablemente la fila de encabezado), saltar
                    continue
                try:
                    x_min = float(parts[2].replace(',', '.'))
                    y_min = float(parts[3].replace(',', '.'))
                    x_max = float(parts[4].replace(',', '.'))
                    y_max = float(parts[5].replace(',', '.'))
                except Exception:
                    # si alguno de los valores no es convertible, saltar la línea
                    continue
                indicadores.append({
                    'Clase': clase,
                    'Confianza': confianza,
                    'x_min': x_min,
                    'y_min': y_min,
                    'x_max': x_max,
                    'y_max': y_max
                })
    return indicadores
