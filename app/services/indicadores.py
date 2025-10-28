def extraer_indicadores(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = f.read()
        
    indicadores = []
    lines = data.split('\n')
    start_extracting = False
    
    header_skipped = False 

    for line in lines:
        if 'Detecciones:' in line:
            start_extracting = True
            continue
        
        if start_extracting:
            if '------' in line or line.strip() == '':
                continue
            
            if not header_skipped:
                header_skipped = True
                continue
            
            parts = line.split() 
            
            if len(parts) >= 6:
                clase = parts[0]
                
                raw_conf = parts[1]
                raw_conf_clean = raw_conf.strip().rstrip('%').replace(',', '.')
                
                try:
                    confianza = float(raw_conf_clean)
                    
                    x_min = float(parts[2].replace(',', '.'))
                    y_min = float(parts[3].replace(',', '.'))
                    x_max = float(parts[4].replace(',', '.'))
                    y_max = float(parts[5].replace(',', '.'))
                    
                except ValueError:
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