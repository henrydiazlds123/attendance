import os
import polib
import csv

def extract_msgid_from_po(po_file):
    try:
        # Cargar el archivo PO
        po = polib.pofile(po_file)
    except OSError as e:
        print(f"Error al leer el archivo .po: {e}")
        return []
    
    # Extraer los msgid (solo cadenas de texto, sin contextos adicionales)
    msgids = [entry.msgid for entry in po if entry.msgid]
    
    return msgids

def save_msgid_to_csv(msgids, output_file):
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['msgid'])
        for msgid in msgids:
            writer.writerow([msgid])

# Obtener la ruta del directorio en el que se ejecuta el script
current_directory = os.path.dirname(os.path.realpath(__file__))

# Definir la ruta del archivo .po en el mismo directorio
po_file = os.path.join(current_directory, 'messages.po')
output_file = os.path.join(current_directory, 'msgids.csv')

# Extraer los msgids
msgids = extract_msgid_from_po(po_file)

# Si se encontraron msgids, guardarlos en un archivo CSV
if msgids:
    save_msgid_to_csv(msgids, output_file)
    print(f'{len(msgids)} msgids extracted and saved to {output_file} successfully!')
else:
    print("No msgids found or error reading the file.")
