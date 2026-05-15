import { create } from 'zustand';

export interface Vehicle {
  id: string;
  type: 'fire' | 'police' | 'ambulance';
  latitude: number;
  longitude: number;
  heading: number; // For rotating the marker icon
}

export interface CrisisZone {
  id: string;
  latitude: number;
  longitude: number;
  radius: number;
  severity: number;
}

interface MapState {
  vehicles: Record<string, Vehicle>;
  crisisZones: Record<string, CrisisZone>;
  updateVehiclePosition: (vehicle: Vehicle) => void;
  setZones: (zones: CrisisZone[]) => void;
}

// Global store for the Map
// Using Zustand over React Context prevents full component tree re-renders
// when a single vehicle coordinate updates every 100ms.
export const useMapStore = create<MapState>((set) => ({
  vehicles: {},
  crisisZones: {},
  
  updateVehiclePosition: (vehicle) =>
    set((state) => ({
      vehicles: { ...state.vehicles, [vehicle.id]: vehicle },
    })),
    
  setZones: (zones) => {
    // Convert array to dictionary for O(1) lookups
    const zonesDict = zones.reduce((acc, z) => ({ ...acc, [z.id]: z }), {});
    set({ crisisZones: zonesDict });
  },
}));
