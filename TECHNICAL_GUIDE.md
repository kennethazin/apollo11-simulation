# Apollo Mission visualisation: Technical Guide

## 1. Project Motivation

This project aims to create an accurate visualisation of the Apollo 11 mission, specifically focusing on the trajectory and navigation aspects of the journey from Earth to the Moon. The motivation behind this project is to:

- Provide an interactive and visually engaging way to understand the complex orbital mechanics of the Apollo missions
- Create an accurate representation based on historical NASA mission data
- Demonstrate the engineering challenges overcome during the Apollo program
- Educate users about space travel mechanics and the historical significance of lunar exploration

The visualisation combines accurate physics-based simulations with modern web technologies to create an immersive experience that transitions from Earth launch to lunar landing.

## 2. Research and Historical Data

The project relies heavily on historical NASA mission documentation to ensure accuracy in the simulation. Key research areas included:a

- Launch parameters of the Saturn V rocket
- Orbital transfer mechanics between Earth and Moon
- Trans-Lunar Injection (TLI) burn specifics
- Lunar Module descent and ascent trajectories
- Apollo landing site coordinates
- Mission timelines and key event sequences

Historical sources included:

- NASA Apollo Flight Journal
- Apollo Mission Reports
- Saturn V post-flight trajectory analysis documents
- Lunar Module performance specifications
- Apollo Guidance Computer documentation

Of particular importance was accurately representing the multi-stage nature of the mission, including:

- Earth launch and orbit
- Trans-Lunar Injection
- Lunar orbit insertion
- Lunar module descent and landing
- Lunar module ascent and rendezvous

## 3. System Architecture

### 3.1 Frontend Components

The frontend is built with React and uses CesiumJS for 3D visualisation of both Earth and lunar scenes. Key components include:

- **EarthScene**: Renders the Earth, Saturn V launch, and orbital trajectory
- **MoonScene**: Renders the lunar surface, landing sites, and lunar module trajectory
- **App**: Manages the transition between Earth and Moon scenes based on mission timeline

### 3.2 Backend Components

A Rust-based emulation of the Apollo Guidance Computer (AGC) serves as the backend. This provides:

- Historical accuracy in navigation calculations
- Period-appropriate limitations in computational resources, mirroring the constraints faced by the Apollo 11 crew
- Authentic behavior of the guidance systems

### 3.3 Data Pipeline

Python scripts generate CZML (Cesium Language) files containing trajectory data, which are then consumed by the CesiumJS components to visualise the mission. This approach allows:

- Accurate physical modeling of rocket dynamics
- Integration of historical flight data
- Realistic representation of complex orbital mechanics

### 3.4 Technology Stack

- **Frontend**: React, TypeScript, CesiumJS
- **Build System**: Vite
- **Trajectory Generation**: Python with NumPy, SciPy, Matplotlib
- **Backend**: Rust (Apollo 11 AGC emulation running Comanche and Luminary binaries)
- **Data Format**: CZML (Cesium Language)

## 4. Implementation Details

### 4.1 Earth Launch Simulation

The Earth launch simulation models the Saturn V rocket's three-stage ascent to orbit and Trans-Lunar Injection burn. The simulation:

- Models realistic thrust, mass flow, and aerodynamic effects
- Implements multi-stage separation and burn sequences
- Applies accurate gravitational models
- Creates a visual with realistic rocket orientation during flight

Key implementation features include:

- Velocity orientation property for realistic rocket alignment
- Particle system for rocket exhaust display
- Visual effects for stage separation
- Post-processing lens flare for atmospheric effects

### 4.2 Lunar Operations

The lunar scene provides visualisation of:

- Lunar terrain using 3D tiles
- Historical Apollo landing sites as points of interest
- Lunar Module descent and ascent trajectories
- Surface operations and exploration

Implementation highlights:

- Custom lunar terrain from Cesium Ion assets
- Height-referenced labeling of landing sites
- CZML-based animation of the Lunar Module trajectory
- Camera controls for viewing the scene from multiple perspectives

### 4.3 Physics-Based Trajectory Generation

Python scripts use numerical integration to solve the equations of motion for:

- Earth-to-orbit launch
- Trans-lunar injection
- Lunar descent
- Lunar ascent

The scripts implement:

- Atmospheric drag models (for Earth)
- Multi-stage propulsion
- Gravity models

### 4.4 CZML Data Format

The project uses CZML (Cesium Language) as the data interchange format between the physics simulation and visualisation. This format:

- Defines time-dependent position and orientation
- Specifies visual properties of objects
- Controls availability of entities based on mission timeline
- Stores path visualisation properties

## 5. Code Analysis

### 5.1 Earth Launch Trajectory Generation

From the Python script `saturn_v_orbit_orientiation.py`, we can see the approach to modeling the Saturn V launch:

```python
# Rocket Geometry
diam = 10.0584  # m (33 ft converted to meters)
A = np.pi / 4 * (diam)**2  # m² frontal area
CD = 0.515  # Drag coefficient

# Stage 1
mprop = 2077000  # kg propellant mass
mstruc = 137000  # kg structural mass
mpl = 43500  # kg payload mass
tburn1 = 168  # s burn time
Thrust = 34500000  # N thrust
m_dot = mprop / tburn1  # kg/s propellant mass flow rate
```

This accurately models the physical properties of the Saturn V and its stages. The differential equations governing motion are:

```python
def derivatives(t,y):
    v = y[0] # m/s
    psi = y[1] # radians
    theta = y[2]
    h = y[3]
    # determine gravity and drag
    g = g0 / (1 + h / Re) ** 2
    rho = rho0 * np.exp(-h / hscale)
    D = 1 / 2 * rho * v**2 * A * CD

    # if statements to determine the thrust and mass
    if t < tburn1:
        m = m0 - m_dot*t
        T = Thrust
    elif t < tburn1 + tburn2: # after stage 1 burn, start burning stage 2
        m = m0s2 - m_dot2 * (t-tburn1) # set mass of vehicle, subtracting out original burn time
        T = Thrusts2 # set thrust to stage 2 thrust
    # ... more stages ...

    ## differential equations
    if h <= hturn: # before the pitch over height
        psi_dot = 0 # change in flight path angle is 0
        v_dot = T / m - D / m - g # change in velocity
        theta_dot = 0 # change in downrange angle is just earths rotation
        h_dot = v # change in height is simply velocity
    else:
        phi_dot = g * np.sin(psi) / v
        v_dot = T / m - D / m - g * np.cos(psi)
        h_dot = v * np.cos(psi)
        theta_dot = v* np.sin(psi) / (Re + h)
        psi_dot = phi_dot - theta_dot
    return [v_dot, psi_dot, theta_dot, h_dot]
```

These equations capture the complex dynamics of the launch, including gravity, drag, and the multi-stage nature of the Saturn V.

### 5.2 Lunar Module Trajectory

The lunar module trajectory is similarly modeled in `moon_orbit.py`, with specific parameters for the lunar environment:

```python
# Constants
omega = 2.6617e-6         # rad/s, Moon rotation rate
Re = 1737100              # m, lunar radius
g0 = 1.62                 # m/s², surface gravity
mu = g0 * Re**2           # m³/s², gravitational parameter

# LM Ascent Stage Parameters
Thrust = 15600 * 3.3      # N, Increased thrust (corrected from Apollo data)
Isp = 311                 # s, specific impulse
mstruc = 2175             # kg, dry mass
mprop = 2372              # kg, propellant mass
mpl = 250                 # kg, payload (astronauts, samples, etc.)
```

The guidance algorithm for the lunar module uses a pitch program to control ascent trajectory:

```python
def pitch_program(t):
    """Returns the target pitch angle at time t"""
    if t < vertical_rise_time:
        return 90 * deg  # Vertical rise
    elif t < vertical_rise_time + pitch_over_duration:
        # Modified pitch profile with slower initial rotation
        elapsed = t - vertical_rise_time
        frac = elapsed / pitch_over_duration
        # Non-linear pitch program for better performance
        pitch_angle = 90 * deg * (1 - np.sin(frac * np.pi/2))
        return max(pitch_angle, final_pitch)
    else:
        return final_pitch  # Horizontal flight
```

### 5.3 CesiumJS Implementation

In the React components, CesiumJS is used to visualise the generated trajectories. For example, in `EarthScene.tsx`:

```typescript
// Set up a clock event listener
const onTickListener = () => {
  if (!viewerRef.current || sceneSwitchTriggeredRef.current) return;

  const currentTime = viewerRef.current.clock.currentTime;
  const correctedTliEndTime = Cesium.JulianDate.fromIso8601(
    "1969-07-16T17:05:54Z"
  );

  // Logic for switching tracked entity (SaturnV -> Post-TLI)
  if (
    viewerRef.current.trackedEntity === satellite &&
    Cesium.JulianDate.compare(currentTime, correctedTliEndTime) >= 0
  ) {
    console.log(
      "Switching tracked entity to Post-TLI at",
      Cesium.JulianDate.toIso8601(currentTime)
    );
    satellite.show = false;
    postTLI.show = true;
    if (postTLI.path) {
      postTLI.path.show = new Cesium.ConstantProperty(true);
    }
    viewerRef.current.trackedEntity = postTLI;
  }
```

This code handles the transition between the Saturn V and CSM-LM configuration after TLI, demonstrating how the mission timeline is managed in the visualisation.

### 5.4 Particle Effects for Rocket Engines

A notable implementation detail is the particle system for visualising rocket exhaust:

```typescript
// Particle system for thrusters
const thrusterParticles = new Cesium.ParticleSystem({
  image: "/image.png", // Path to particle image
  startColor: Cesium.Color.RED.withAlpha(0.7),
  endColor: Cesium.Color.YELLOW.withAlpha(0.3),
  startScale: 1.0,
  endScale: 4.0,
  minimumParticleLife: 0.5,
  maximumParticleLife: 1.5,
  minimumSpeed: 5.0,
  maximumSpeed: 10.0,
  emissionRate: 50,
  emitter: new Cesium.ConeEmitter(Cesium.Math.toRadians(30)),
  modelMatrix: Cesium.Matrix4.IDENTITY,
  lifetime: 16.0,
});
```

The system dynamically positions the thruster particles based on the rocket's current orientation and only activates during burn phases:

```typescript
function updateThrusterParticles() {
  const currentJulianTime = viewer.clock.currentTime;

  // Define burn times using JulianDate for accurate comparison
  const burnIntervals = [
    new Cesium.TimeInterval({
      start: Cesium.JulianDate.fromIso8601("1969-07-16T13:32:00Z"),
      stop: Cesium.JulianDate.fromIso8601("1969-07-16T13:34:48Z"),
    }), // Stage 1
    // ... more stages ...
  ];

  // Check if current time is within any burn interval
  const isBurning = burnIntervals.some((interval) =>
    Cesium.TimeInterval.contains(interval, currentJulianTime)
  );

  thrusterParticles.show = isBurning && activeEntity === satellite;
```

## 6. Challenges and Solutions

### 6.1 Accurate Physics Modeling

**Challenge**: Balancing physical accuracy with performance requirements.

**Solution**: Used simplified but accurate physical models that capture essential dynamics while remaining computationally efficient:

- Implemented multi-stage rocket equations with changing mass
- Modeled atmospheric drag with exponential density model
- Used proper gravitational models for both Earth and Moon

### 6.2 Scene Transitions

**Challenge**: Creating a seamless transition from Earth to lunar scenes.

**Solution**: Implemented an event-based transition system that:

- Detects when the Trans-Lunar Injection burn completes
- Gracefully destroys the Earth scene
- Initializes the Moon scene with the appropriate initial conditions
- Maintains continuity in the mission timeline

### 6.3 Memory Management

**Challenge**: CesiumJS components can be memory-intensive, especially when running multiple scenes.

**Solution**:

- Implemented careful cleanup of resources when transitioning scenes
- Used references to properly track and dispose of Cesium viewers
- Added explicit event listener removal to prevent memory leaks

```typescript
// Cleanup function
return () => {
  console.log("Cleaning up EarthScene");
  // Remove the specific onTick listener if it's still active
  if (onTickListenerRemoverRef.current) {
    console.log("Removing onTick listener");
    onTickListenerRemoverRef.current();
    onTickListenerRemoverRef.current = undefined;
  }
  // Destroy the viewer instance
  if (viewerRef.current && !viewerRef.current.isDestroyed()) {
    console.log("Destroying Cesium viewer");
    viewerRef.current.destroy();
  }
  viewerRef.current = null;
```

### 6.4 Accurate Historical Timeline

**Challenge**: Synchronizing simulation time with historical mission events.

**Solution**:

- Used actual mission timestamps for event triggers
- Implemented a mission clock that follows the historical timeline
- Created linkages between simulation time and real mission events

```typescript
// Define the time to trigger the scene switch
const earthSceneEndTime = Cesium.JulianDate.fromIso8601(
  "1969-07-16T18:00:00Z" // Time when Earth scene should end
);

// Check if the current time has reached the end time and trigger the scene switch callback
if (
  !sceneSwitchTriggeredRef.current && // Only trigger once
  Cesium.JulianDate.compare(currentTime, earthSceneEndTime) >= 0
) {
  console.log(
    "Earth scene end time reached at",
    Cesium.JulianDate.toIso8601(currentTime)
  );
  sceneSwitchTriggeredRef.current = true; // Mark as triggered
  onEarthSceneEnd(); // Call the callback passed from App.jsx
}
```

## 7. Results

The completed project delivers:

1. A physically accurate simulation of the Apollo mission trajectory
2. Interactive visualisation of both Earth and lunar operations
3. Realistic 3D models of the Saturn V rocket and Lunar Module
4. Timeline-based progression through mission phases
5. Visually engaging effects for rocket engines and environmental factors
6. Educational markers for Apollo landing sites
7. Camera controls that allow exploration of the mission from multiple perspectives

The visualisation provides insights into:

- The multi-stage nature of the Saturn V launch
- The complex orbital mechanics of Trans-Lunar Injection
- The precision required for lunar landings
- The engineering achievements of the Apollo program

## 8. Future Work

Several areas for enhancement have been identified:

### 8.1 Enhanced AGC Integration

The Rust-based Apollo Guidance Computer emulation could be more tightly integrated with the visualisation, allowing:

- Real-time execution of actual AGC code
- visualisation of the guidance algorithms in action
- Interactive demonstration of navigation techniques

### 8.2 VR/AR Support

Extending the project to support Virtual and Augmented Reality would enhance the immersive experience:

- VR headset compatibility for first-person perspectives
- AR capabilities for educational demonstrations
- Mobile support for broader accessibility

### 8.3 Mission Variations

Expanding to include multiple Apollo missions would provide comparative educational value:

- Different landing sites and approach trajectories
- Failed mission scenarios (like Apollo 13)
- Alternative mission profiles

### 8.4 Interactive Controls

Adding user-controllable aspects would increase engagement:

- Manual thruster control options
- Guidance parameter adjustments
- "What-if" scenario exploration

### 8.5 Educational Extensions

Incorporating more educational content would enhance the learning value:

- Interactive explanations of orbital mechanics concepts
- Historical context and mission background
- Technical details about spacecraft systems

## 9. Conclusion

This Apollo mission visualisation project successfully combines historical accuracy, physical simulation, and modern web technologies to create an engaging educational tool. By leveraging React, CesiumJS, Python for trajectory generation, and Rust for AGC emulation, the project creates a comprehensive representation of one of humanity's greatest technological achievements.

The implementation balances technical accuracy with performance requirements, creating a visualisation that is both educational and engaging. The modular architecture allows for future expansion and enhancement, ensuring the project can grow to include more features and capabilities.
