# CIRO - React Native Expo Project Structure

This document outlines the frontend architecture for the CIRO mobile application using modern React Native practices.

## 1. Recommended Libraries
To meet the requirements for modularity, performance, and real-time capabilities:
* **Core:** `expo` (latest SDK), `react-native`, `typescript`
* **Navigation:** `expo-router` (File-based routing, ideal for deep linking and simplified navigation)
* **State Management (Client):** `zustand` (Lightweight, boilerplate-free global state for UI and Auth)
* **State Management (Server):** `@tanstack/react-query` (Caching, polling, and API state)
* **Maps:** `react-native-maps` (Supports Google Maps integration and custom dark themes)
* **Styling:** `nativewind` (Tailwind CSS for React Native) - enables fast, consistent tactical dark mode UI.
* **Realtime:** `socket.io-client` or `@supabase/supabase-js` (for WebSockets)
* **Notifications:** `expo-notifications`

---

## 2. Folder Structure
A feature-based, highly modular architecture designed to scale.

```text
ciro-mobile/
├── app/                      # Expo Router (File-based navigation)
│   ├── (auth)/               # Authentication Stack
│   │   ├── sign-in.tsx
│   │   └── _layout.tsx
│   ├── (tabs)/               # Main Bottom Tabs Navigation
│   │   ├── dashboard.tsx
│   │   ├── map.tsx
│   │   ├── feed.tsx
│   │   ├── analytics.tsx
│   │   └── _layout.tsx
│   ├── crisis/               # Nested detail routes
│   │   ├── [id].tsx          # Dynamic Crisis Detail Screen
│   │   ├── actions.tsx       # Emergency Actions authorization
│   │   └── ai-reasoning.tsx
│   ├── _layout.tsx           # Root layout (Providers, Theme, Auth Gate)
│   └── +not-found.tsx
├── src/                      # Source Code
│   ├── components/           # Reusable UI Components
│   │   ├── core/             # Buttons, Inputs, Typography, Cards
│   │   ├── maps/             # LiveMap, MapMarkers, HeatmapLayer
│   │   └── crisis/           # EmergencyBadge, ConfidenceRing, Timeline
│   ├── hooks/                # Custom React Hooks
│   │   ├── useAuth.ts
│   │   ├── useLocation.ts
│   │   └── useRealtime.ts    # WebSocket connection management
│   ├── services/             # API Service Layer
│   │   ├── apiClient.ts      # Axios instance with interceptors
│   │   ├── crisisApi.ts      # Endpoints for crisis data
│   │   └── agentApi.ts       # Endpoints for Agent triggers/logs
│   ├── store/                # Zustand Stores
│   │   ├── authStore.ts
│   │   ├── mapStore.ts       # Real-time unit coordinates
│   │   └── filterStore.ts    # Map UI filters
│   ├── theme/                # Design System & Colors
│   │   ├── colors.ts         # Tactical Dark Mode palette
│   │   ├── mapStyle.json     # Google Maps custom dark theme
│   │   └── typography.ts
│   ├── types/                # Global TypeScript Interfaces
│   │   └── index.ts
│   └── utils/                # Helpers & Formatters
│       └── formatting.ts
├── assets/                   # Images, Fonts, Icons
├── .env                      # Environment Variables
├── app.json                  # Expo config (Bundle ID, Maps API keys)
├── babel.config.js
└── package.json
```

---

## 3. Navigation Setup (Expo Router)
With `expo-router`, the `/app` directory drives the navigation:
* `app/_layout.tsx`: The Root layout initializes the `QueryClientProvider` (React Query) and `ThemeProvider`. It observes the Zustand `authStore` and uses a `<Slot />` to render the app, redirecting to `(auth)/sign-in` if `isAuthenticated` is false.
* `app/(tabs)/_layout.tsx`: Configures the bottom tab bar with custom tactical icons and dark background styling.
* `app/crisis/[id].tsx`: Handles dynamic routing. Uses `useLocalSearchParams()` to extract the `id` and fetch the specific crisis data via React Query.

---

## 4. State Management (Zustand & React Query)

### Global UI State (Zustand)
Used for synchronous, client-side state (e.g., Auth, Map Filters, UI Toggles).
```typescript
// src/store/authStore.ts
import { create } from 'zustand';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  setAuth: (user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  setAuth: (user) => set({ user, isAuthenticated: true }),
  logout: () => set({ user: null, isAuthenticated: false }),
}));
```

### Server State (React Query)
Used for all API interactions to handle caching, loading states, and background refetching.
```typescript
// Example React Query Hook
export const useActiveCrises = () => {
  return useQuery({
    queryKey: ['crises', 'active'],
    queryFn: () => crisisApi.fetchActive(),
    staleTime: 1000 * 60, // 1 minute
  });
};
```

---

## 5. Realtime Updates & Notifications

### WebSockets (`useRealtime.ts`)
A custom hook initialized in the Root Layout. It connects to the backend WebSocket. 
* **Event: `CRISIS_NEW`**: Triggers `queryClient.invalidateQueries(['crises'])` to force React Query to fetch the latest list.
* **Event: `UNIT_MOVED`**: Directly updates the `mapStore` with new coordinates for emergency vehicles (bypassing React Query for high-frequency, low-latency UI updates).

### Push Notifications
Configured using `expo-notifications`. Upon successful login, the app requests notification permissions, retrieves the Expo Push Token, and sends it to the FastAPI backend. Notifications are handled via a listener in the Root layout to route the user directly to `app/crisis/[id].tsx` when tapped.

---

## 6. Environment Configuration
Managed via standard `.env` files, mapped to Expo's `process.env`.
```env
EXPO_PUBLIC_API_URL=https://api.ciro.app/v1
EXPO_PUBLIC_WS_URL=wss://api.ciro.app/ws
EXPO_PUBLIC_GOOGLE_MAPS_API_KEY=AIzaSy...
```

---

## 7. Reusable UI Components
* **`<LiveMap />`**: A wrapper around `MapView` (`react-native-maps`) that automatically applies the `src/theme/mapStyle.json` (dark mode map) and renders custom `<Marker>` components based on the `mapStore`.
* **`<TacticalCard />`**: A foundational container component with a deep navy background (`#1A2235`) and optional neon glowing borders.
* **`<EmergencyBadge level="critical" />`**: Returns dynamically colored pill badges (Red, Orange, Green) based on the severity prop.
* **`<AIConfidenceRing />`**: An SVG-based circular progress indicator showing the Agent's certainty score.
