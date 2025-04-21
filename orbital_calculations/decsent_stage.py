import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_ivp
import os
import json
import datetime

# Constants
omega = 2.6617e-6         # rad/s, Moon rotation rate
Re = 1737100              # m, lunar radius
g0 = 1.62                 # m/s², surface gravity
mu = g0 * Re**2           # m³/s², gravitational parameter
deg = np.pi / 180         # degrees to radians

# LM Descent Stage Parameters
Thrust = 45000             # N, descent engine thrust
Isp = 311                  # s, specific impulse
mstruc = 2200              # kg, dry mass
mprop = 8200               # kg, propellant mass
mpl = 500                  # kg, payload (astronauts, equipment, etc.)
tburn = 750                # s, burn duration (approximate)
m_dot = Thrust / (Isp * 9.81)  # kg/s, mass flow rate

m0 = mstruc + mprop + mpl

# Initial Conditions for Descent
v0 = 1600                  # m/s, orbital velocity at 15 km altitude
gamma0 = -1 * deg          # initial flight path angle (slightly downward)
r0 = Re + 15000            # m, initial radius (15 km altitude)
theta0 = 0                 # initial angular position
t_max = 2000               # total sim time (s)

# Target Landing Parameters
target_altitude = 0        # m, surface altitude
target_radius = Re         # m, lunar surface radius

# Adjusted Pitch Program for Descent
def pitch_program(t):
    """Returns the target pitch angle at time t for descent"""
    if t < 100:
        return -5 * deg  # Initial descent angle
    elif t < 500:
        return -45 * deg  # Steeper descent
    else:
        return -90 * deg  # Vertical descent

# Adjusted Throttle Program for Descent
def throttle_program(t, h, v):
    """Returns thrust fraction based on time and state for descent"""
    if h < 1000:  # Close to the surface
        return 0.3  # Low throttle for soft landing
    return 1.0  # Full thrust otherwise

def derivatives(t, state):
    """Calculates state derivatives in a rotating reference frame"""
    r, theta, v, gamma, m = state
    
    # Calculate local gravity
    g = mu / r**2
    
    # Determine if engine is burning and remaining propellant
    remaining_propellant = m - (mstruc + mpl)
    if t < tburn and remaining_propellant > 0:
        throttle = throttle_program(t, r - Re, v)
        T = Thrust * throttle
        mdot = -m_dot * throttle
    else:
        T = 0
        mdot = 0
    
    # Target pitch from guidance
    gamma_target = pitch_program(t)
    
    # Simple proportional control for pitch rate with rate limiting
    K_p = 0.1  # Proportional gain
    max_rate = 0.5 * deg  # Maximum pitch rate (deg/s)
    desired_rate = K_p * (gamma_target - gamma)
    gamma_dot = np.clip(desired_rate, -max_rate, max_rate)
    
    # State derivatives
    r_dot = v * np.sin(gamma)
    theta_dot = v * np.cos(gamma) / r
    
    # Acceleration components
    a_thrust = T / m
    a_gravity = -g
    a_centripetal = v**2 * np.cos(gamma)**2 / r  # Centripetal acceleration
    
    # Velocity derivative (corrected with all components)
    v_dot = a_thrust + a_gravity * np.sin(gamma) + a_centripetal * np.sin(gamma)
    
    return [r_dot, theta_dot, v_dot, gamma_dot, mdot]

# Event function for reaching the surface
def reach_surface(t, state):
    r, theta, v, gamma, m = state
    return r - target_radius
reach_surface.terminal = True
reach_surface.direction = -1  # Trigger when crossing from above

# Event function for propellant depletion 
def propellant_depleted(t, state):
    r, theta, v, gamma, m = state
    return m - (mstruc + mpl) - 1.0  # 1kg margin
propellant_depleted.terminal = False
propellant_depleted.direction = -1  # Only trigger when crossing from above

# Initial state for descent
initial_state = [r0, theta0, v0, gamma0, m0]

# Solve the descent trajectory
sol = solve_ivp(
    derivatives,
    [0, t_max],
    initial_state,
    method='RK45',
    events=[reach_surface, propellant_depleted],
    rtol=1e-6,
    atol=1e-8,
    max_step=1.0
)

# Extract results
t = sol.t
r = sol.y[0]
theta = sol.y[1]
v = sol.y[2]
gamma = sol.y[3]
m = sol.y[4]

h = r - Re                     # m, altitude
h_km = h / 1000                # km, altitude
v_km_s = v / 1000              # km/s, velocity
gamma_deg = gamma / deg        # deg, flight path angle
dx = r * np.sin(theta)         # m, x-position
dy = r * np.cos(theta)         # m, y-position
downrange = theta * Re / 1000  # km, downrange distance

# Print results
print("\n--- Apollo 11 Lunar Module Descent Simulation Results ---")
print(f"Simulation time: {t[-1]:.1f} seconds")
print(f"Final Altitude: {h_km[-1]:.2f} km")
print(f"Final Velocity: {v_km_s[-1]:.4f} km/s")
print(f"Final Flight Path Angle: {gamma_deg[-1]:.2f} degrees")
print(f"Downrange Distance: {downrange[-1]:.2f} km")
print(f"Propellant Remaining: {m[-1] - mstruc - mpl:.2f} kg")
print(f"Reason for termination: {'Landed on surface' if r[-1] <= target_radius else 'Propellant depleted'}")

plt.figure(figsize=(15, 10))

# Altitude vs Time
plt.subplot(2, 3, 1)
plt.plot(t, h_km)
plt.axhline(y=target_altitude, color='r', linestyle='--', label='Target Altitude')
plt.title('Altitude vs Time')
plt.xlabel('Time (s)')
plt.ylabel('Altitude (km)')
plt.grid(True)
plt.legend()

# Velocity vs Time
plt.subplot(2, 3, 2)
plt.plot(t, v_km_s)
plt.title('Velocity vs Time')
plt.xlabel('Time (s)')
plt.ylabel('Velocity (km/s)')
plt.grid(True)

# Flight Path Angle vs Time
plt.subplot(2, 3, 3)
plt.plot(t, gamma_deg)
plt.title('Flight Path Angle vs Time')
plt.xlabel('Time (s)')
plt.ylabel('Flight Path Angle (deg)')
plt.grid(True)

# Trajectory in Lunar Reference Frame
plt.subplot(2, 3, 4)
# Plot the Moon
moon_circle = plt.Circle((0, 0), Re/1000, color='gray', alpha=0.3)
plt.gca().add_patch(moon_circle)

# Plot the trajectory
plt.plot(dx/1000, dy/1000, 'b-')
plt.axis('equal')
plt.title('Trajectory (Lunar Reference Frame)')
plt.xlabel('X (km)')
plt.ylabel('Y (km)')
plt.grid(True)

# Downrange vs Altitude
plt.subplot(2, 3, 5)
plt.plot(downrange, h_km)
plt.title('Trajectory Profile')
plt.xlabel('Downrange Distance (km)')
plt.ylabel('Altitude (km)')
plt.grid(True)

# Mass vs Time
plt.subplot(2, 3, 6)
plt.plot(t, m)
plt.axhline(y=mstruc+mpl, color='r', linestyle='--', label='Dry Mass')
plt.title('Vehicle Mass vs Time')
plt.xlabel('Time (s)')
plt.ylabel('Mass (kg)')
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()

plt.figure(figsize=(15, 5))

# Acceleration vs Time
plt.subplot(1, 3, 1)
plt.plot(t, accel)
plt.title('Acceleration vs Time')
plt.xlabel('Time (s)')
plt.ylabel('Acceleration (m/s²)')
plt.grid(True)

# Mass Flow Rate
plt.subplot(1, 3, 2)
m_flow = np.zeros_like(t)
for i in range(len(t)-1):
    m_flow[i] = (m[i+1] - m[i])/(t[i+1] - t[i])
plt.plot(t[:-1], -m_flow[:-1])  # Negative because mass decreases
plt.title('Mass Flow Rate vs Time')
plt.xlabel('Time (s)')
plt.ylabel('Mass Flow Rate (kg/s)')
plt.grid(True)

# Guidance vs Actual Flight Path Angle
plt.subplot(1, 3, 3)
guidance_angle = np.array([pitch_program(time) for time in t])
plt.plot(t, guidance_angle/deg, 'r--', label='Guidance')
plt.plot(t, gamma_deg, 'b-', label='Actual')
plt.title('Guidance vs Actual Flight Path Angle')
plt.xlabel('Time (s)')
plt.ylabel('Angle (deg)')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()

# Set the epoch to the actual date and time of Apollo 11 lunar module descent
epoch = datetime.datetime(1969, 7, 20, 17, 44, 0)  # UTC time of lunar module descent initiation

# Generate CZML data
czml = [
    {
        "id": "document",
        "name": "LM Descent Trajectory",
        "version": "1.0",
        "clock": {
            "interval": f"{epoch.isoformat()}Z/{(epoch + datetime.timedelta(seconds=t_max)).isoformat()}Z",
            "currentTime": f"{epoch.isoformat()}Z",
            "range": "LOOP_STOP",
            "step": "SYSTEM_CLOCK_MULTIPLIER"
        }
    }
]

# Add descent stage trajectory
descent_positions = []
for i in range(len(t)):
    x = r[i] * np.sin(theta[i])
    y = r[i] * np.cos(theta[i])
    z = 0  # Assume motion in the lunar equatorial plane
    descent_positions.extend([t[i], x, y, z])

czml.append({
    "id": "DescentStage",
    "availability": f"{epoch.isoformat()}Z/{(epoch + datetime.timedelta(seconds=t_max)).isoformat()}Z",
    "path": {
        "leadTime": 0,
        "material": {
            "solidColor": {
                "color": {
                    "rgba": [255, 0, 0, 255]  # Red color for descent stage
                }
            }
        },
        "width": 2,
        "show": True
    },
    "position": {
        "interpolationAlgorithm": "LINEAR",
        "epoch": epoch.isoformat() + "Z",
        "cartesian": descent_positions
    },
   "model": {
        "gltf": "/models/lm/lunarmodule.gltf",
        "minimumPixelSize": 64,
        "maximumScale": 20000
    }
})

# Write CZML to file
czml_file_path = os.path.join(os.path.dirname(__file__), "lm_descent_trajectory.czml")
with open(czml_file_path, "w") as czml_file:
    json.dump(czml, czml_file, indent=2)

print(f"CZML file written to {czml_file_path}")