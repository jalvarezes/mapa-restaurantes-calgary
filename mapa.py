import folium
import csv

# Crear un mapa centrado en Calgary
calgary_coords = [51.0447, -114.0719]
m = folium.Map(location=calgary_coords, zoom_start=12)

# Leer restaurantes desde el archivo CSV y agregarlos al mapa
with open("restaurantes.csv", newline="", encoding="utf-8") as csvfile:
    lector = csv.DictReader(csvfile)
    for fila in lector:
        nombre = fila["nombre"]
        direccion = fila["direccion"]
        notas = fila.get("notas", "").strip()
        latitud = float(fila["latitud"])
        longitud = float(fila["longitud"])
        estatus = fila["estatus"].strip().lower()

        # Elegir color según el estatus
        if estatus == "cliente":
            color = "green"
        else:  # prospecto u otro valor
            color = "red"

        # Construir el texto que aparecerá en la ventana al hacer clic
        popup_texto = (
            f"<b>Nombre:</b> {nombre}<br>"
            f"<b>Dirección:</b> {direccion}<br>"
            f"<b>Estatus:</b> {estatus.capitalize()}<br>"
        )
        if notas:
            popup_texto += f"<b>Notas:</b> {notas}"

        folium.Marker(
            location=[latitud, longitud],
            popup=popup_texto,
            tooltip=nombre,
            icon=folium.Icon(color=color)
        ).add_to(m)

# Guardar el mapa en un archivo HTML
m.save("mapa_restaurantes_calgary.html")

print("Mapa creado: abre 'mapa_restaurantes_calgary.html' en tu navegador.")
