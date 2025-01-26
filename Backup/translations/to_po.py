import os
import csv
import polib

def create_po_file(language_code, translations, output_directory):
    # Crear un objeto PO
    po = polib.POFile()
    
    # Añadir metadatos al archivo .po
    po.metadata = {
        'Content-Type': 'text/plain; charset=UTF-8',
        'Language': language_code,
    }
    
    # Agregar las traducciones al archivo .po
    for msgid, translation in translations.items():
        entry = polib.POEntry(
            msgid=msgid,
            msgstr=translation
        )
        po.append(entry)
    
    # Guardar el archivo .po
    output_file = os.path.join(output_directory, f"{language_code}.po")
    po.save(output_file)
    print(f"Archivo .po generado: {output_file}")

def read_translations_from_csv(csv_file):
    translations_es = {}
    translations_pt = {}
    
    # Leer el archivo CSV
    with open(csv_file, 'r', encoding='utf-16') as file:
        reader = csv.DictReader(file, delimiter='\t')
        for row in reader:
            # Suponemos que las columnas son: en, es, pt
            english_text = row['en']
            translations_es[english_text] = row['es']
            translations_pt[english_text] = row['pt']
    
    return translations_es, translations_pt

# Ruta del archivo CSV y directorio de salida
csv_file = 'translations.csv'  # Asegúrate de que esté en el mismo directorio o especifica la ruta completa
output_directory = os.path.dirname(os.path.realpath(__file__))

# Leer las traducciones desde el archivo CSV
translations_es, translations_pt = read_translations_from_csv(csv_file)

# Crear los archivos .po para español e portugués
create_po_file('es', translations_es, output_directory)
create_po_file('pt', translations_pt, output_directory)
