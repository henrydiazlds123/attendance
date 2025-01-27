import polib
from collections import defaultdict

def find_duplicates(po_file):
    # Cargar el archivo .po
    po = polib.pofile(po_file)
    
    # Diccionario para contar las ocurrencias de cada msgid
    msgid_counts = defaultdict(list)
    
    # Recorrer las entradas del archivo .po
    for i, entry in enumerate(po, start=1):
        msgid_counts[entry.msgid].append(i)  # Usar el índice como línea aproximada
    
    # Buscar duplicados (msgid con más de una ocurrencia)
    duplicates = {msgid: lines for msgid, lines in msgid_counts.items() if len(lines) > 1}
    
    return duplicates

def main():
    po_file = "messages.po"  # Nombre del archivo .po (debe estar en el mismo directorio)
    
    try:
        duplicates = find_duplicates(po_file)
        if duplicates:
            print("Duplicados encontrados:")
            for msgid, lines in duplicates.items():
                print(f"  - msgid: {msgid}")
                print(f"    Líneas aproximadas: {', '.join(map(str, lines))}")
        else:
            print("No se encontraron duplicados.")
    except Exception as e:
        print(f"Error procesando el archivo {po_file}: {e}")

if __name__ == "__main__":
    main()
