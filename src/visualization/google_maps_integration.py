"""
Google Maps Integration for Campus Energy Visualization.

Visualizes campus energy consumption on Google Maps with:
- Building-level energy usage heatmap
- Real-time sensor locations
- Energy flow visualization
- Interactive markers for solar panels, batteries, and buildings
"""

import json
from typing import Dict, List, Tuple, Optional
import pandas as pd
from dataclasses import dataclass


@dataclass
class BuildingLocation:
    """Represents a building on campus."""
    id: str
    name: str
    latitude: float
    longitude: float
    type: str  # academic, residential, administrative, etc.
    floor_area_sqm: float
    typical_load_kw: float


@dataclass
class SensorLocation:
    """Represents an energy sensor/meter location."""
    id: str
    name: str
    latitude: float
    longitude: float
    sensor_type: str  # solar, battery, meter, weather
    current_value: float
    unit: str


class CampusEnergyMapGenerator:
    """
    Generate interactive Google Maps visualizations of campus energy.

    Creates HTML with embedded Google Maps showing:
    - Building energy consumption (color-coded by intensity)
    - Solar panel locations
    - Battery storage systems
    - Energy flow between systems
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize map generator.

        Parameters
        ----------
        api_key : str, optional
            Google Maps API key. If None, uses a demo map center.
        """
        self.api_key = api_key or "YOUR_GOOGLE_MAPS_API_KEY"

    def get_sample_campus_layout(self) -> Tuple[List[BuildingLocation], List[SensorLocation], Tuple[float, float]]:
        """
        Get sample campus layout with buildings and sensors.

        Returns
        -------
        tuple
            (buildings, sensors, campus_center)
        """
        # Example: Generic university campus (can be customized)
        campus_center = (12.9716, 77.5946)  # Bangalore coordinates (example)

        buildings = [
            BuildingLocation("B1", "Engineering Block", 12.9720, 77.5940, "academic", 5000, 150),
            BuildingLocation("B2", "Science Labs", 12.9718, 77.5950, "academic", 3000, 120),
            BuildingLocation("B3", "Library", 12.9715, 77.5945, "academic", 2000, 80),
            BuildingLocation("B4", "Student Hostel A", 12.9710, 77.5935, "residential", 4000, 200),
            BuildingLocation("B5", "Student Hostel B", 12.9708, 77.5940, "residential", 4000, 200),
            BuildingLocation("B6", "Administrative Block", 12.9722, 77.5948, "administrative", 2500, 100),
            BuildingLocation("B7", "Sports Complex", 12.9712, 77.5955, "sports", 3500, 90),
            BuildingLocation("B8", "Auditorium", 12.9717, 77.5938, "events", 1500, 60),
        ]

        sensors = [
            SensorLocation("S1", "Solar Array 1 (Rooftop)", 12.9720, 77.5940, "solar", 150, "kW"),
            SensorLocation("S2", "Solar Array 2 (Parking)", 12.9710, 77.5938, "solar", 100, "kW"),
            SensorLocation("S3", "Battery Storage", 12.9716, 77.5942, "battery", 75, "% SoC"),
            SensorLocation("S4", "Main Grid Connection", 12.9716, 77.5946, "meter", 180, "kW"),
            SensorLocation("S5", "Weather Station", 12.9716, 77.5946, "weather", 28, "°C"),
        ]

        return buildings, sensors, campus_center

    def calculate_energy_intensity(
        self,
        current_load_kw: float,
        floor_area_sqm: float
    ) -> str:
        """
        Calculate energy intensity and return color code.

        Parameters
        ----------
        current_load_kw : float
            Current power consumption
        floor_area_sqm : float
            Building floor area

        Returns
        -------
        str
            Color code: green (low), yellow (medium), orange (high), red (very high)
        """
        # Energy intensity in W/sqm
        intensity = (current_load_kw * 1000) / floor_area_sqm

        if intensity < 20:
            return "green"
        elif intensity < 40:
            return "yellow"
        elif intensity < 60:
            return "orange"
        else:
            return "red"

    def generate_map_html(
        self,
        buildings: List[BuildingLocation],
        sensors: List[SensorLocation],
        campus_center: Tuple[float, float],
        current_energy_data: Optional[Dict] = None,
        output_file: str = "campus_energy_map.html"
    ) -> str:
        """
        Generate interactive Google Maps HTML.

        Parameters
        ----------
        buildings : List[BuildingLocation]
            Campus buildings
        sensors : List[SensorLocation]
            Energy sensors
        campus_center : tuple
            (latitude, longitude) of campus center
        current_energy_data : dict, optional
            Current energy readings by building ID
        output_file : str
            Output HTML filename

        Returns
        -------
        str
            Path to generated HTML file
        """
        if current_energy_data is None:
            # Use typical loads as fallback
            current_energy_data = {b.id: b.typical_load_kw for b in buildings}

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Campus Energy Digital Twin - Map View</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
        }}
        #map {{
            height: 100vh;
            width: 100%;
        }}
        .legend {{
            position: absolute;
            bottom: 30px;
            right: 30px;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 1000;
            font-size: 14px;
        }}
        .legend-title {{
            font-weight: bold;
            margin-bottom: 10px;
            font-size: 16px;
        }}
        .legend-item {{
            margin: 8px 0;
            display: flex;
            align-items: center;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
            margin-right: 10px;
            border: 1px solid #ccc;
        }}
        .info-panel {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 1000;
            max-width: 350px;
        }}
        .info-title {{
            font-weight: bold;
            font-size: 18px;
            margin-bottom: 15px;
            color: #2c3e50;
        }}
        .info-stat {{
            margin: 10px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }}
        .stat-label {{
            font-size: 12px;
            color: #6c757d;
            text-transform: uppercase;
        }}
        .stat-value {{
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            margin-top: 5px;
        }}
        .refresh-btn {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: #007bff;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 1000;
        }}
        .refresh-btn:hover {{
            background: #0056b3;
        }}
    </style>
</head>
<body>
    <div id="map"></div>

    <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Data</button>

    <div class="info-panel">
        <div class="info-title">🏛️ Campus Energy Overview</div>
        <div class="info-stat">
            <div class="stat-label">Total Campus Load</div>
            <div class="stat-value" id="total-load">-- kW</div>
        </div>
        <div class="info-stat">
            <div class="stat-label">Solar Generation</div>
            <div class="stat-value" id="solar-gen">-- kW</div>
        </div>
        <div class="info-stat">
            <div class="stat-label">Battery SoC</div>
            <div class="stat-value" id="battery-soc">-- %</div>
        </div>
        <div class="info-stat">
            <div class="stat-label">Grid Import</div>
            <div class="stat-value" id="grid-import">-- kW</div>
        </div>
    </div>

    <div class="legend">
        <div class="legend-title">Energy Intensity</div>
        <div class="legend-item">
            <div class="legend-color" style="background: #28a745;"></div>
            <span>Low (&lt; 20 W/m²)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #ffc107;"></div>
            <span>Medium (20-40 W/m²)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #fd7e14;"></div>
            <span>High (40-60 W/m²)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #dc3545;"></div>
            <span>Very High (&gt; 60 W/m²)</span>
        </div>
        <hr style="margin: 15px 0;">
        <div class="legend-title">Sensors</div>
        <div class="legend-item">
            <span style="font-size: 20px; margin-right: 10px;">☀️</span>
            <span>Solar Panels</span>
        </div>
        <div class="legend-item">
            <span style="font-size: 20px; margin-right: 10px;">🔋</span>
            <span>Battery Storage</span>
        </div>
        <div class="legend-item">
            <span style="font-size: 20px; margin-right: 10px;">⚡</span>
            <span>Grid Connection</span>
        </div>
    </div>

    <script>
        // Energy data
        const buildingData = {json.dumps([{
            'id': b.id,
            'name': b.name,
            'lat': b.latitude,
            'lng': b.longitude,
            'type': b.type,
            'area': b.floor_area_sqm,
            'current_load': current_energy_data.get(b.id, b.typical_load_kw),
            'typical_load': b.typical_load_kw
        } for b in buildings])};

        const sensorData = {json.dumps([{
            'id': s.id,
            'name': s.name,
            'lat': s.latitude,
            'lng': s.longitude,
            'type': s.sensor_type,
            'value': s.current_value,
            'unit': s.unit
        } for s in sensors])};

        const campusCenter = {{lat: {campus_center[0]}, lng: {campus_center[1]}}};

        function initMap() {{
            // Create map
            const map = new google.maps.Map(document.getElementById('map'), {{
                zoom: 16,
                center: campusCenter,
                mapTypeId: 'satellite',
                mapTypeControl: true,
                streetViewControl: false,
                fullscreenControl: true
            }});

            // Calculate total stats
            let totalLoad = 0;
            let solarGen = 0;
            let batterySoc = 0;
            let gridImport = 0;

            // Add building markers
            buildingData.forEach(building => {{
                const intensity = (building.current_load * 1000) / building.area;
                let color;
                if (intensity < 20) color = '#28a745';
                else if (intensity < 40) color = '#ffc107';
                else if (intensity < 60) color = '#fd7e14';
                else color = '#dc3545';

                const marker = new google.maps.Marker({{
                    position: {{lat: building.lat, lng: building.lng}},
                    map: map,
                    title: building.name,
                    icon: {{
                        path: google.maps.SymbolPath.CIRCLE,
                        scale: 12,
                        fillColor: color,
                        fillOpacity: 0.8,
                        strokeColor: '#ffffff',
                        strokeWeight: 2
                    }}
                }});

                const infoWindow = new google.maps.InfoWindow({{
                    content: `
                        <div style="padding: 10px; min-width: 200px;">
                            <h3 style="margin: 0 0 10px 0; color: #2c3e50;">${{building.name}}</h3>
                            <p style="margin: 5px 0;"><strong>Type:</strong> ${{building.type}}</p>
                            <p style="margin: 5px 0;"><strong>Floor Area:</strong> ${{building.area.toLocaleString()}} m²</p>
                            <p style="margin: 5px 0;"><strong>Current Load:</strong> <span style="color: ${{color}}; font-weight: bold;">${{building.current_load.toFixed(1)}} kW</span></p>
                            <p style="margin: 5px 0;"><strong>Intensity:</strong> ${{intensity.toFixed(1)}} W/m²</p>
                            <p style="margin: 5px 0; font-size: 11px; color: #6c757d;">Typical: ${{building.typical_load.toFixed(1)}} kW</p>
                        </div>
                    `
                }});

                marker.addListener('click', () => {{
                    infoWindow.open(map, marker);
                }});

                totalLoad += building.current_load;
            }});

            // Add sensor markers
            sensorData.forEach(sensor => {{
                let icon;
                if (sensor.type === 'solar') {{
                    icon = '☀️';
                    solarGen += sensor.value;
                }} else if (sensor.type === 'battery') {{
                    icon = '🔋';
                    batterySoc = sensor.value;
                }} else if (sensor.type === 'meter') {{
                    icon = '⚡';
                    gridImport = sensor.value;
                }} else if (sensor.type === 'weather') {{
                    icon = '🌡️';
                }} else {{
                    icon = '📊';
                }}

                const marker = new google.maps.Marker({{
                    position: {{lat: sensor.lat, lng: sensor.lng}},
                    map: map,
                    title: sensor.name,
                    label: {{
                        text: icon,
                        fontSize: '24px'
                    }}
                }});

                const infoWindow = new google.maps.InfoWindow({{
                    content: `
                        <div style="padding: 10px; min-width: 200px;">
                            <h3 style="margin: 0 0 10px 0; color: #2c3e50;">${{sensor.name}}</h3>
                            <p style="margin: 5px 0;"><strong>Type:</strong> ${{sensor.type}}</p>
                            <p style="margin: 5px 0;"><strong>Current Value:</strong> <span style="font-size: 18px; font-weight: bold; color: #007bff;">${{sensor.value.toFixed(1)}} ${{sensor.unit}}</span></p>
                            <p style="margin: 5px 0; font-size: 11px; color: #6c757d;">Click refresh button to update</p>
                        </div>
                    `
                }});

                marker.addListener('click', () => {{
                    infoWindow.open(map, marker);
                }});
            }});

            // Update summary stats
            document.getElementById('total-load').textContent = totalLoad.toFixed(1) + ' kW';
            document.getElementById('solar-gen').textContent = solarGen.toFixed(1) + ' kW';
            document.getElementById('battery-soc').textContent = batterySoc.toFixed(1) + ' %';
            document.getElementById('grid-import').textContent = gridImport.toFixed(1) + ' kW';
        }}
    </script>
    <script src="https://maps.googleapis.com/maps/api/js?key={self.api_key}&callback=initMap" async defer></script>
</body>
</html>"""

        # Write to file
        with open(output_file, 'w') as f:
            f.write(html_content)

        print(f"\n✓ Google Maps visualization generated: {output_file}")
        print(f"  Open this file in a web browser to view the interactive map")
        print(f"  Note: Replace 'YOUR_GOOGLE_MAPS_API_KEY' with actual API key for production use")

        return output_file

    def generate_energy_flow_diagram_html(
        self,
        solar_kw: float,
        demand_kw: float,
        battery_kw: float,
        grid_import_kw: float,
        grid_export_kw: float,
        output_file: str = "energy_flow.html"
    ) -> str:
        """
        Generate Sankey diagram showing energy flows.

        Parameters
        ----------
        solar_kw : float
            Solar generation
        demand_kw : float
            Campus demand
        battery_kw : float
            Battery charge/discharge (positive = charging)
        grid_import_kw : float
            Grid import
        grid_export_kw : float
            Grid export
        output_file : str
            Output HTML filename

        Returns
        -------
        str
            Path to generated HTML file
        """
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Campus Energy Flow Diagram</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        #chart {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }}
        h1 {{
            text-align: center;
            color: #2c3e50;
        }}
    </style>
</head>
<body>
    <h1>🔋 Campus Energy Flow - Real-Time</h1>
    <div id="chart"></div>

    <script>
        // Define energy flows
        const data = [{{
            type: "sankey",
            orientation: "h",
            node: {{
                pad: 15,
                thickness: 30,
                line: {{
                    color: "black",
                    width: 0.5
                }},
                label: ["Solar", "Grid Import", "Battery", "Campus Demand", "Grid Export"],
                color: ["#f39c12", "#3498db", "#27ae60", "#e74c3c", "#95a5a6"]
            }},
            link: {{
                source: [0, 0, 1, 2, 0, 2],
                target: [3, 2, 3, 3, 4, 4],
                value: [
                    {max(0, solar_kw - battery_kw - grid_export_kw)},
                    {max(0, battery_kw)},
                    {grid_import_kw},
                    {max(0, -battery_kw)},
                    {grid_export_kw},
                    0
                ]
            }}
        }}];

        const layout = {{
            title: "Energy Flow Distribution",
            font: {{
                size: 14
            }},
            height: 600
        }};

        Plotly.newPlot('chart', data, layout);
    </script>
</body>
</html>"""

        with open(output_file, 'w') as f:
            f.write(html_content)

        print(f"\n✓ Energy flow diagram generated: {output_file}")
        return output_file


def main():
    """Generate sample campus energy map."""
    print("=" * 70)
    print("Campus Energy Map Generator")
    print("=" * 70)

    generator = CampusEnergyMapGenerator()

    # Get sample campus layout
    buildings, sensors, campus_center = generator.get_sample_campus_layout()

    print(f"\nCampus Configuration:")
    print(f"  Buildings: {len(buildings)}")
    print(f"  Sensors: {len(sensors)}")
    print(f"  Center: {campus_center}")

    # Generate map with current data
    current_energy = {
        "B1": 180,  # Engineering Block - high usage
        "B2": 95,   # Science Labs - medium
        "B3": 60,   # Library - low
        "B4": 220,  # Hostel A - high
        "B5": 210,  # Hostel B - high
        "B6": 85,   # Admin - medium
        "B7": 110,  # Sports - medium
        "B8": 45,   # Auditorium - low
    }

    map_file = generator.generate_map_html(
        buildings=buildings,
        sensors=sensors,
        campus_center=campus_center,
        current_energy_data=current_energy,
        output_file="campus_energy_map.html"
    )

    # Generate energy flow diagram
    flow_file = generator.generate_energy_flow_diagram_html(
        solar_kw=250,
        demand_kw=400,
        battery_kw=-50,  # Discharging
        grid_import_kw=180,
        grid_export_kw=0,
        output_file="energy_flow.html"
    )

    print("\n" + "=" * 70)
    print("Files Generated:")
    print("=" * 70)
    print(f"1. {map_file} - Interactive campus energy map")
    print(f"2. {flow_file} - Energy flow diagram")
    print("\n✓ Open these files in a web browser to visualize campus energy!")
    print("\nNote: For production use, obtain a Google Maps API key from:")
    print("https://developers.google.com/maps/documentation/javascript/get-api-key")


if __name__ == "__main__":
    main()
