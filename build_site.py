import os
import json

OUTPUT_DIR = r"c:\Users\lukec\Pictures\Postcards\letter\website"
IMAGE_DIR = "images"
TOTAL_POSTCARDS = 37
PALETTE = ["#007bff", "#28a745", "#fd7e14", "#6f42c1", "#17a2b8", "#e83e8c"]

os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADER = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="styles.css">
    
    <!-- Leaflet Map -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="muni.js"></script>

    <script src="script.js" defer></script>
    {extra_head}
</head>
<body>
    <header>
        <h1>Pompton Lakes Postcard Archive</h1>
    </header>
"""

FOOTER = """
</body>
</html>
"""

FILTER_SCRIPT = """
<script>
function filterSelection(c) {
    var x = document.getElementsByClassName("gallery-item");
    for (var i = 0; i < x.length; i++) {
        x[i].style.display = "none";
        var tagsAttr = x[i].getAttribute("data-tags");
        if (c === "all" || (tagsAttr && tagsAttr.includes(c))) {
            x[i].style.display = "block";
        }
    }
    var btns = document.getElementsByClassName("filter-btn");
    for (var i = 0; i < btns.length; i++) {
        btns[i].classList.remove("active");
        if (btns[i].dataset.filter === c) {
            btns[i].classList.add("active");
        }
    }
}
document.addEventListener("DOMContentLoaded", () => { filterSelection('all'); });
</script>
"""

def build_site():
    print(f"Building site from database.geojson in {OUTPUT_DIR}...")
    
    geo_path = os.path.join(OUTPUT_DIR, "database.geojson")
    if not os.path.exists(geo_path):
        print("ERROR: database.geojson not found!")
        return

    with open(geo_path, "r", encoding="utf-8") as f:
        db = json.load(f)

    loc_map = {f["id"]: f["properties"]["name"] for f in db.get("features", [])}
    cat_map = {c["id"]: c["name"] for c in db.get("categories", [])}
    
    # 1. Build index.html
    index_content = HEADER.format(title="Pompton Lakes Postcard Archive", extra_head=FILTER_SCRIPT)
    
    index_content += '<div class="filters">\n'
    index_content += '    <button class="filter-btn active" data-filter="all" onclick="filterSelection(\'all\')">All</button>\n'
            
    if cat_map:
        for c_id, c_name in cat_map.items():
            index_content += f'    <button class="filter-btn" data-filter="{c_id}" onclick="filterSelection(\'{c_id}\')">{c_name}</button>\n'
            
    index_content += '</div>\n'
    
    index_content += '<main class="gallery-grid">\n'

    global_map_features = []

    for pc in db.get("postcards", []):
        num_str = f"{pc['id']:03d}"
        thumb_img = f"thumbnails/thumb_{num_str}.jpg"
        page_link = f"postcard{num_str}.html"
        
        filter_ids = set()
        if pc.get("global_categories"):
            filter_ids.update(pc["global_categories"])
        for box in pc.get("boxes", []):
            if box.get("categories"):
                filter_ids.update(box["categories"])
                
        tags_html = '<div class="tags">'
        for c_id in filter_ids:
            tags_html += f'<span class="tag tag-cat">{cat_map.get(c_id, c_id)}</span>'
        tags_html += '</div>'
        
        filter_json = json.dumps(list(filter_ids))
        
        index_content += f"""
        <a href="{page_link}" class="gallery-item" data-tags='{filter_json}'>
            <img src="{thumb_img}" alt="Postcard {num_str}" loading="lazy">
            <h3>Postcard {num_str}</h3>
            {tags_html}
        </a>
        """

        # Map features for Index Map
        if pc.get("global_location_id"):
            l_id = pc["global_location_id"]
            loc_feature = next((f for f in db.get("features", []) if f["id"] == l_id), None)
            if loc_feature and loc_feature.get("geometry"):
                lng, lat = loc_feature["geometry"]["coordinates"]
                global_map_features.append({
                    "lat": lat, "lng": lng, "name": f"Postcard {num_str}",
                    "angle": pc.get("viewshed_angle", 0),
                    "fov": pc.get("viewshed_fov", 120),
                    "radius": pc.get("viewshed_radius", 100),
                    "color": "#ff3b30",
                    "url": page_link,
                    "thumb": thumb_img
                })
        for idx, box in enumerate(pc.get("boxes", [])):
            if box.get("location_id"):
                l_id = box["location_id"]
                loc_feature = next((f for f in db.get("features", []) if f["id"] == l_id), None)
                if loc_feature and loc_feature.get("geometry"):
                    lng, lat = loc_feature["geometry"]["coordinates"]
                    global_map_features.append({
                        "lat": lat, "lng": lng, "name": f"Postcard {num_str} (Part {idx+1})",
                        "angle": box.get("viewshed_angle", 0),
                        "fov": box.get("viewshed_fov", 120),
                        "radius": box.get("viewshed_radius", 100),
                        "color": PALETTE[idx % len(PALETTE)],
                        "url": page_link,
                        "thumb": thumb_img
                    })

    index_content += '</main>\n'
    
    # Global Map at the bottom of the index
    if global_map_features:
        avg_lat = sum(f["lat"] for f in global_map_features) / len(global_map_features)
        avg_lng = sum(f["lng"] for f in global_map_features) / len(global_map_features)
        global_map_json = json.dumps(global_map_features)
        
        index_content += f"""
        <div class="index-map-container" style="max-width: 1200px; margin: 40px auto; padding: 0 20px;">
            <h2>Mapped Postcards</h2>
            <p style="color:#666; margin-bottom:15px;">Select a point on the map below to view the approximate location and viewshed of specific postcards.</p>
            <div id="index-map" style="width: 100%; height: 500px; border-radius: 8px; border: 1px solid #ccc; box-shadow: 0 4px 12px rgba(0,0,0,0.05);"></div>
            <script>
            document.addEventListener("DOMContentLoaded", () => {{
                const features = {global_map_json};
                if (features.length === 0) return;
                
                const map = L.map('index-map').setView([{avg_lat}, {avg_lng}], 14);
                
                const esriStreet = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{ attribution: 'Tiles © Esri' }});
                const esriSat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{ attribution: 'Tiles © Esri' }});
                const esriSatLabels = L.layerGroup([
                    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{ attribution: 'Tiles © Esri' }}),
                    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{{z}}/{{y}}/{{x}}')
                ]);
                
                esriStreet.addTo(map);
                L.control.layers({{
                    "Street Map": esriStreet,
                    "Satellite": esriSat,
                    "Satellite (with Labels)": esriSatLabels
                }}).addTo(map);
                
                if (typeof muniGeoJSON !== 'undefined') {{
                    L.geoJSON(muniGeoJSON, {{
                        style: function (feature) {{
                            return {{color: "#555", weight: 2, fillOpacity: 0.1}};
                        }}
                    }}).addTo(map);
                }}
                
                const bounds = L.latLngBounds();
                const viewshedLayer = L.featureGroup().addTo(map);
                
                // Group features by exact coordinates
                const grouped = {{}};
                features.forEach(f => {{
                    const key = f.lat + ',' + f.lng;
                    if (!grouped[key]) grouped[key] = {{ lat: f.lat, lng: f.lng, items: [] }};
                    grouped[key].items.push(f);
                }});
                
                Object.values(grouped).forEach(g => {{
                    bounds.extend([g.lat, g.lng]);
                    const marker = L.marker([g.lat, g.lng]).addTo(map);
                    
                    let popupContent = '<div style="text-align:center; max-height:250px; overflow-y:auto; padding-right:10px;">';
                    g.items.forEach(f => {{
                        popupContent += `
                            <div style="margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px;">
                                <strong>${{f.name}}</strong><br>
                                <a href="${{f.url}}"><img src="${{f.thumb}}" style="width:120px; margin-top:8px; border-radius:4px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);"></a><br>
                                <a href="${{f.url}}" style="display:inline-block; margin-top:8px; font-weight:bold; color:#007bff; text-decoration:none;">View Details</a>
                            </div>
                        `;
                    }});
                    popupContent += '</div>';
                    marker.bindPopup(popupContent);
                    
                    marker.on('click', () => {{
                        viewshedLayer.clearLayers();
                        g.items.forEach(f => {{
                            const points = [[f.lat, f.lng]];
                            const R = 6378137;
                            const start = f.angle - (f.fov / 2);
                            const end = f.angle + (f.fov / 2);
                            for (let i = start; i <= end; i += 5) {{
                                const rad = i * Math.PI / 180;
                                const dLat = (f.radius * Math.cos(rad)) / R;
                                const dLng = (f.radius * Math.sin(rad)) / (R * Math.cos(f.lat * Math.PI / 180));
                                points.push([
                                    f.lat + dLat * (180 / Math.PI),
                                    f.lng + dLng * (180 / Math.PI)
                                ]);
                            }}
                            L.polygon(points, {{color: f.color || '#ff3b30', fillOpacity: 0.25, weight: 2}}).addTo(viewshedLayer);
                        }});
                    }});
                }});
                
                if (features.length > 1) {{
                    map.fitBounds(bounds, {{padding: [50, 50]}});
                }}
            }});
            </script>
        </div>
        """

    index_content += FOOTER

    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_content)
    print("Created index.html")

    # 2. Build postcard pages
    for pc in db.get("postcards", []):
        num_str = f"{pc['id']:03d}"
        front_img = f"{IMAGE_DIR}/postcard{num_str}.jpg"
        back_img = f"{IMAGE_DIR}/back{num_str}.jpg"
        
        page_content = HEADER.format(title=f"Postcard {num_str} - Pompton Lakes Archive", extra_head="")
        
        # Aggregate tags
        cat_to_boxes = {}
        for c_id in pc.get("global_categories", []):
            if c_id not in cat_to_boxes:
                cat_to_boxes[c_id] = []
                
        boxes_html = ''
        for idx, box in enumerate(pc.get("boxes", [])):
            color = PALETTE[idx % len(PALETTE)]
            left, top, width, height = box["x"]*100, box["y"]*100, box["w"]*100, box["h"]*100
            boxes_html += f'''
            <div class="bounding-box box-{idx}" style="left:{left}%; top:{top}%; width:{width}%; height:{height}%; border-color:{color};">
                <span class="box-label" style="background:{color}; color:white; padding:2px 6px; font-size:12px; font-weight:bold; position:absolute; top:0; left:0;">Part {idx+1}</span>
            </div>
            '''
            for c_id in box.get("categories", []):
                if c_id not in cat_to_boxes:
                    cat_to_boxes[c_id] = []
                cat_to_boxes[c_id].append(str(idx))

        tags_html = '<div class="tags" style="margin-bottom: 20px;">'
        for c_id, boxes in cat_to_boxes.items():
            data_attr = f' data-box="{",".join(boxes)}"' if boxes else ''
            tags_html += f'<span class="tag tag-cat"{data_attr}>{cat_map.get(c_id, c_id)}</span>'
        tags_html += '</div>'
        
        # Map Logic
        map_features = []
        
        # Global Location
        if pc.get("global_location_id"):
            l_id = pc["global_location_id"]
            loc_feature = next((f for f in db.get("features", []) if f["id"] == l_id), None)
            if loc_feature and loc_feature.get("geometry"):
                lng, lat = loc_feature["geometry"]["coordinates"]
                map_features.append({
                    "lat": lat, "lng": lng, "name": loc_map.get(l_id, "Unnamed Location"),
                    "angle": pc.get("viewshed_angle", 0),
                    "fov": pc.get("viewshed_fov", 120),
                    "radius": pc.get("viewshed_radius", 100),
                    "color": "#ff3b30"
                })
                
        # Box Locations
        for idx, box in enumerate(pc.get("boxes", [])):
            if box.get("location_id"):
                l_id = box["location_id"]
                loc_feature = next((f for f in db.get("features", []) if f["id"] == l_id), None)
                if loc_feature and loc_feature.get("geometry"):
                    lng, lat = loc_feature["geometry"]["coordinates"]
                    map_features.append({
                        "lat": lat, "lng": lng, "name": f"{loc_map.get(l_id, 'Unnamed Location')} (Part {idx+1})",
                        "angle": box.get("viewshed_angle", 0),
                        "fov": box.get("viewshed_fov", 120),
                        "radius": box.get("viewshed_radius", 100),
                        "color": PALETTE[idx % len(PALETTE)]
                    })

        map_html = ""
        if map_features:
            avg_lat = sum(f["lat"] for f in map_features) / len(map_features)
            avg_lng = sum(f["lng"] for f in map_features) / len(map_features)
            map_features_json = json.dumps(map_features)
            
            map_html = f"""
            <div class="postcard-view map-view" style="margin-top: 40px; margin-bottom: 40px;">
                <h3>Approximate Location + Viewshed</h3>
                <div id="map" style="width: 100%; height: 400px; border-radius: 8px; border: 1px solid #ccc; box-shadow: 0 4px 12px rgba(0,0,0,0.05);"></div>
                <script>
                document.addEventListener("DOMContentLoaded", () => {{
                    const features = {map_features_json};
                    if (features.length === 0) return;
                    
                    const map = L.map('map').setView([{avg_lat}, {avg_lng}], 15);
                    
                    const esriStreet = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{ attribution: 'Tiles © Esri' }});
                    const esriSat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{ attribution: 'Tiles © Esri' }});
                    const esriSatLabels = L.layerGroup([
                        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{ attribution: 'Tiles © Esri' }}),
                        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{{z}}/{{y}}/{{x}}')
                    ]);
                    
                    esriStreet.addTo(map);
                    L.control.layers({{
                        "Street Map": esriStreet,
                        "Satellite": esriSat,
                        "Satellite (with Labels)": esriSatLabels
                    }}).addTo(map);
                    
                    if (typeof muniGeoJSON !== 'undefined') {{
                        L.geoJSON(muniGeoJSON, {{
                            style: function (feature) {{
                                return {{color: "#555", weight: 2, fillOpacity: 0.1}};
                            }}
                        }}).addTo(map);
                    }}
                    
                    const bounds = L.latLngBounds();
                    
                    features.forEach(f => {{
                        L.marker([f.lat, f.lng]).addTo(map).bindPopup('<b>' + f.name + '</b>');
                        bounds.extend([f.lat, f.lng]);
                        
                        const points = [[f.lat, f.lng]];
                        const R = 6378137;
                        const start = f.angle - (f.fov / 2);
                        const end = f.angle + (f.fov / 2);
                        for (let i = start; i <= end; i += 5) {{
                            const rad = i * Math.PI / 180;
                            const dLat = (f.radius * Math.cos(rad)) / R;
                            const dLng = (f.radius * Math.sin(rad)) / (R * Math.cos(f.lat * Math.PI / 180));
                            points.push([
                                f.lat + dLat * (180 / Math.PI),
                                f.lng + dLng * (180 / Math.PI)
                            ]);
                        }}
                        L.polygon(points, {{color: f.color || '#ff3b30', fillOpacity: 0.3, weight: 2}}).addTo(map);
                    }});
                    
                    if (features.length > 1) {{
                        map.fitBounds(bounds, {{padding: [50, 50]}});
                    }}
                }});
                </script>
            </div>
            """
        
        page_content += f"""
    <main class="postcard-detail">
        <a href="index.html" class="back-link">← Back to Gallery</a>
        <h2>Postcard {num_str}</h2>
        {tags_html}
        
        <div class="postcard-images">
            <div class="postcard-view">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h3 style="margin: 0;">Front</h3>
                    <button onclick="document.getElementById('front-wrapper-{num_str}').classList.toggle('hide-boxes')" style="cursor: pointer; padding: 5px 10px; background: #6c757d; color: white; border: none; border-radius: 4px; font-size: 14px;">Show Tagged Views</button>
                </div>
                <div class="image-wrapper" id="front-wrapper-{num_str}">
                    <img src="{front_img}" alt="Postcard {num_str} Front">
                    {boxes_html}
                </div>
            </div>
            
            <div class="postcard-view">
                <h3>Back</h3>
                <img src="{back_img}" alt="Postcard {num_str} Back">
            </div>
        </div>
        
        {map_html}
    </main>
        """
        page_content += FOOTER
        
        with open(os.path.join(OUTPUT_DIR, f"postcard{num_str}.html"), "w", encoding="utf-8") as f:
            f.write(page_content)

    print(f"Successfully generated {len(db.get('postcards', []))} postcard detail pages.")

if __name__ == "__main__":
    build_site()
