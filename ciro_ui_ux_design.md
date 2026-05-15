# CIRO - UI/UX Design System & Screen Blueprint

![CIRO Mobile Dashboard Concept](file:///C:/Users/dell/.gemini/antigravity/brain/95124619-65db-4217-8c99-27d9e1d715ae/artifacts/ciro_dashboard_mockup_1778865201570.png)

## 1. Design Aesthetic & Core Principles
* **Theme:** Tactical Dark Mode. Designed to reduce eye strain for night-time operation and enhance contrast for critical emergency alerts.
* **Vibe:** Futuristic, clean, professional, and high-urgency without causing panic.
* **Colors:**
    * **Background:** Tactical Black (`#0B0F19`)
    * **Surface:** Deep Navy (`#1A2235`)
    * **Primary Accent:** Electric Blue (`#3B82F6`) - Standard info, map markers, and primary buttons.
    * **Alert Colors:** 
        * Critical: Neon Red (`#EF4444`)
        * Warning: Cyber Orange (`#F97316`)
        * Resolved/Safe: Emerald Green (`#10B981`)
* **Typography:**
    * **Headings:** `Outfit` (Modern, geometric, clean).
    * **Data/Numbers/Logs:** `Roboto Mono` or `Inter` (Highly legible for coordinates, scores, timestamps, and tech data).

## 2. Component Hierarchy
1. **`<LiveMapCard />`**: Embedded map view with dark tiles, glowing heatmap overlays, and pulsating alert markers.
2. **`<EmergencyBadge level="critical" />`**: Pill-shaped badge with a high-contrast icon and glowing neon border.
3. **`<ConfidenceRing score={92} />`**: Circular progress indicator showing AI certainty. 
4. **`<StatusTimeline eventList={events} />`**: Vertical stepper showing event progression from detection to execution.
5. **`<AIRecommendationBlock />`**: A card with a distinct glowing border, containing an AI-generated text summary and one-tap action buttons.

## 3. Navigation Flow
* **Root Navigation (Stack):**
    * `AuthStack` (Splash -> Login/Register -> Biometric Auth)
    * `MainTabNav` (Dashboard, Map, Feed, Analytics)
* **Tab Navigation (Bottom Bar):**
    * **Dashboard:** Home base with high-level overview.
    * **Live Map:** Center tab with prominent floating action button (FAB) for quick views.
    * **Feed:** Chronological feed of social and weather anomalies.
    * **Analytics:** Post-action reports and AI accuracy metrics.
* **Modals & Action Sheets:**
    * `CrisisDetailSheet`: Slides up from bottom when a map marker is tapped.
    * `EmergencyActionsModal`: Takes full screen for critical dispatch authorizations.

---

## 4. Screen Layouts (11 Required Screens)

### 1. Splash Screen
* **Layout:** Centered logo (CIRO text with a futuristic radar/shield emblem) fading in.
* **Background:** Deep Navy with a subtle animated grid overlay.
* **Animation:** Radar sweeps once, then rapidly zooms into a 3D city view to transition into the Auth screen.

### 2. Login/Register
* **Layout:** Minimalist inputs. Biometric login (FaceID/Fingerprint) is centered and prioritized for fast first-responder access.
* **Elements:** Agency Code input, "Emergency Guest" access mode for civilian broadcasting.

### 3. Dashboard
* **Layout:** Top user greeting & status indicator (e.g., "Status: Active Duty - Green").
* **Elements:**
    * **Stats Row:** Active Crises (Red counter), Monitored Signals (Blue counter), Available Units (Green counter).
    * **Map Preview:** Mini interactive map showing the nearest active hot zone.
    * **Recent Alerts List:** Top 3 most urgent pending actions requiring commander authorization.

### 4. Live Crisis Feed
* **Layout:** Infinite scroll list of crisis cards.
* **Elements:** Each card displays: Icon (Fire, Traffic, Weather), Location, AI Confidence Score, Time Elapsed.
* **Interactions:** Swipe right to "Acknowledge", swipe left to "Dismiss".

### 5. Map Screen
* **Layout:** Full-screen immersive map using a dark tactical style.
* **Elements:** Floating search bar at the top. Filter chips underneath (Weather, Social, Traffic, 911 Calls). Glowing heatmap layers over high-density anomaly areas.
* **Interaction:** Tapping a pulsating marker brings up the `Crisis Detail Sheet`.

### 6. Crisis Detail Screen
* **Layout:** Scrollable view with a sticky header.
* **Elements:**
    * Top: `EmergencyBadge` and Incident Title.
    * Middle: `<ConfidenceRing />` alongside a brief 1-sentence AI summary of the situation.
    * Bottom: `<StatusTimeline />` showing exactly when signals were detected and correlated.

### 7. AI Reasoning Screen
* **Layout:** Drill-down from the Crisis Detail, designed to build trust in the AI.
* **Elements:** Visualizes the LangGraph agent chain.
    * Node 1: "Signal Agent: 34 social posts & 2 traffic cams analyzed."
    * Node 2: "Detection Agent: Correlated smoke mentions with weather wind direction."
    * Node 3: "Severity Agent: Calculated Blast Radius: 2.5km. Score: 8.5/10."
* **Animation:** Typewriter effect for AI textual explanations. Nodes connect with flowing neon lines.

### 8. Emergency Actions Screen
* **Layout:** Full screen, high contrast.
* **Elements:** 
    * "Proposed Action Plan": (Step 1: Dispatch Engine 4, Step 2: Issue shelter-in-place for ZIP 90210).
    * Interaction: Massive, glowing **"Swipe to Authorize & Dispatch"** slider at the bottom to prevent accidental taps.
    * "Override" button for manual human-in-the-loop control.

### 9. Notification Center
* **Layout:** Standard list view, accessed via a bell icon (with red dot) top right.
* **Elements:** Segregated via tabs into "System Alerts", "Agent Logs", and "Command Messages".

### 10. System Logs Screen
* **Layout:** Console-style terminal view.
* **Elements:** Raw JSON/Text of agent states, WebSocket pings, and database queries. Very technical, monospace font, green/blue text on black. Useful for debugging and showcasing the technical depth during a hackathon.

### 11. Analytics Dashboard
* **Layout:** Grid of interactive charts.
* **Elements:** Bar charts of average response times, heatmaps of historical crisis hotspots, and AI accuracy metrics.

---

## 5. UI States & Feedback
* **Loading States:** Shimmering dark skeleton loaders over maps and data cards to keep the app feeling fast.
* **Active Alerts:** Slow pulse/breathing glow animation on map markers and critical action buttons.
* **AI Processing:** When generating a plan, a subtle animated gradient border wraps the reasoning card, signaling that the agents are currently "thinking".
* **Transitions:** Smooth slide-up modals for Action Sheets to keep context, and fly-to easing for map navigation to orient the user spatially.
