import pandas as pd

# Ruta al archivo de texto original
file_path = "directorio.txt"  # Cambia la ruta según corresponda

# Leer el archivo de texto
try:
    # Leer el archivo de texto con delimitador tabulador (si es el caso)
    df = pd.read_csv(file_path, sep='\t', encoding='utf-8')
    
    # Convertir el DataFrame a CSV para inspección
    output_csv_path = "archivo_convertido.csv"
    df.to_csv(output_csv_path, index=False)
    
    print(f"Archivo convertido a CSV y guardado en: {output_csv_path}")
    
    # Mostrar las primeras filas del DataFrame para inspección
    print(df.head())

except Exception as e:
    print(f"Hubo un error al leer el archivo de texto: {e}")
