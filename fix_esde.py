import os
import xml.etree.ElementTree as ET
from pathlib import Path

xml_path = Path(r"C:\Users\rammu\ES-DE\settings\es_settings.xml")

if not xml_path.exists():
    print("No se encontró es_settings.xml")
else:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    settings_to_update = {
        "ROMDirectory": r"E:\Carpetas anbernic",
        "MediaDirectory": r"E:\Carpetas anbernic\media"
    }

    for key, value in settings_to_update.items():
        elem = root.find(f"./string[@name='{key}']")
        if elem is not None:
            elem.set('value', value)
        else:
            new_elem = ET.SubElement(root, 'string', {'name': key, 'value': value})

    # Indent for pretty print
    ET.indent(tree, space="    ")
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)
    print("ES-DE configurado localmente.")
