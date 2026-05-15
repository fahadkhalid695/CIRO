import React, { useEffect, useRef } from 'react';
import { View, StyleSheet } from 'react-native';
import MapView, { Marker, Circle, PROVIDER_GOOGLE } from 'react-native-maps';
import { useMapStore } from '../../store/mapStore';

// Tactical Dark Mode Map Styling (Hides POIs, makes roads dark)
const darkMapStyle = [
  { elementType: "geometry", stylers: [{ color: "#212121" }] },
  { elementType: "labels.icon", stylers: [{ visibility: "off" }] },
  { elementType: "labels.text.fill", stylers: [{ color: "#757575" }] },
  { elementType: "labels.text.stroke", stylers: [{ color: "#212121" }] },
  { featureType: "administrative", elementType: "geometry", stylers: [{ color: "#757575" }] },
  { featureType: "water", elementType: "geometry", stylers: [{ color: "#000000" }] }
];

export default function LiveMap() {
  const mapRef = useRef<MapView>(null);
  
  // 1. Optimized Rendering Strategy: 
  // We use Zustand selectors to extract only the values we need.
  const vehicles = useMapStore(state => Object.values(state.vehicles));
  const zones = useMapStore(state => Object.values(state.crisisZones));

  // 2. Realtime WebSocket Connection
  useEffect(() => {
    // In production, this URL would come from process.env.EXPO_PUBLIC_WS_URL
    const ws = new WebSocket('ws://localhost:8000/ws/map-stream');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'VEHICLE_UPDATE') {
        // Direct injection into Zustand prevents full React tree re-renders
        useMapStore.getState().updateVehiclePosition(data.payload);
      } else if (data.type === 'ZONE_UPDATE') {
        useMapStore.getState().setZones(data.payload);
      }
    };

    return () => ws.close();
  }, []);

  return (
    <View style={styles.container}>
      <MapView
        ref={mapRef}
        provider={PROVIDER_GOOGLE}
        style={styles.map}
        customMapStyle={darkMapStyle}
        initialRegion={{
          latitude: 33.6844, // Default to Islamabad/G-10 area for the demo
          longitude: 73.0479,
          latitudeDelta: 0.05,
          longitudeDelta: 0.05,
        }}
        showsUserLocation
        showsTraffic={true} // Built-in Google Maps traffic layer
      >
        {/* Render Emergency Zones (Heatmap Logic) */}
        {zones.map((zone) => (
          <Circle
            key={`zone-${zone.id}`}
            center={{ latitude: zone.latitude, longitude: zone.longitude }}
            radius={zone.radius}
            // Severity Indicators: Darker/Opague Red for high severity
            fillColor={zone.severity > 7 ? 'rgba(239, 68, 68, 0.3)' : 'rgba(249, 115, 22, 0.3)'} 
            strokeColor={zone.severity > 7 ? '#EF4444' : '#F97316'}
            strokeWidth={2}
          />
        ))}

        {/* Render Response Vehicle Simulation */}
        {vehicles.map((vehicle) => (
          <Marker
            key={`vehicle-${vehicle.id}`}
            coordinate={{ latitude: vehicle.latitude, longitude: vehicle.longitude }}
            rotation={vehicle.heading}
            anchor={{ x: 0.5, y: 0.5 }}
          >
            <View style={styles.vehicleMarker}>
              {/* Optional: Add custom SVG icons based on vehicle.type */}
            </View>
          </Marker>
        ))}
      </MapView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0B0F19' },
  map: { width: '100%', height: '100%' },
  vehicleMarker: {
    width: 14,
    height: 14,
    backgroundColor: '#3B82F6', // Tactical Blue marker
    borderRadius: 7,
    borderWidth: 2,
    borderColor: '#FFFFFF',
    shadowColor: '#3B82F6',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 10, // Gives it a glowing effect
  }
});
