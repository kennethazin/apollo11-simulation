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

# CSM Parameters
csm_alt = 110000          # m, CSM orbital altitude (110 km)
csm_radius = Re + csm_alt  # m, CSM orbital radius
csm_velocity = np.sqrt(mu / csm_radius)  # m/s, CSM orbital velocity
csm_period = 2 * np.pi * csm_radius / csm_velocity  # s, CSM orbital period

# LM Stage Parameters
# Descent Stage
LM_Descent_Thrust = 45040  # N, Descent engine thrust
LM_Descent_Isp = 311       # s, specific impulse
LM_Descent_mstruc = 2180   # kg, dry mass
LM_Descent_mprop = 8200    # kg, propellant mass
LM_Descent_tburn = 756     # s, burn duration for descent
LM_Descent_mdot = LM_Descent_Thrust / (LM_Descent_Isp * 9.81)  # kg/s

# Ascent Stage 
LM_Ascent_Thrust = 15600 * 3.3  # N, Ascent engine thrust
LM_Ascent_Isp = 311            # s, specific impulse
LM_Ascent_mstruc = 2175        # kg, dry mass
LM_Ascent_mprop = 2372         # kg, propellant mass
LM_Ascent_mpl = 250            # kg, payload (astronauts, samples, etc.)
LM_Ascent_tburn = 435          # s, burn duration for ascent
LM_Ascent_mdot = LM_Ascent_Thrust / (LM_Ascent_Isp * 9.81)  # kg/s

LM_Descent_m0 = LM_Descent_mstruc + LM_Descent_mprop + LM_Ascent_mstruc + LM_Ascent_mprop + LM_Ascent_mpl
LM_Ascent_m0 = LM_Ascent_mstruc + LM_Ascent_mprop + LM_Ascent_mpl

# Launch Site Coordinates (Apollo 11 landing site)
launch_latitude = 0.67416 * deg  # radians, 0.674 deg N
launch_longitude = 23.47315 * deg  # radians, 23.473 deg E - actual Apollo 11 landing site

# Target Orbit Parameters
target_altitude_km = 111  # km, target orbit altitude (historical)
target_radius = Re + target_altitude_km * 1000  # m
v_target = np.sqrt(mu / target_radius)  # m/s, target orbital velocity

# Simulation time parameters
t_max_descent = 800       # s, max descent sim time
t_max_surface = 7200      # s, surface stay time (2 hours)
t_max_ascent = 1200       # s, max ascent sim time
t_max_rendezvous = 7200   # s, max rendezvous sim time

# CSM Orbit Simulation
def csm_orbit(t, initial_phase):
    """Calculate CSM position at time t with given initial phase"""
    # Orbital period
    period = csm_period
    # Current phase
    phase = initial_phase - (t / period) * 2 * np.pi  
    # Position
    x = csm_radius * np.cos(phase)
    y = csm_radius * np.sin(phase)
    z = 0  # Assuming equatorial orbit
    return x, y, z, phase
# Descent Stage Guidance
def descent_pitch_program(t, altitude, target_alt=0):
    """Returns the target pitch angle for descent at time t and altitude"""
    # Pre-PDI phase (from 19:08 to 20:05) - very shallow trajectory
    if t < pdi_seconds:
        return -1 * deg  # Very shallow descent angle before PDI
    
    # Target approximately 12.5 minutes from PDI to landing
    target_descent_duration = 12.5 * 60  # 12.5 minutes in seconds
    
    # Calculate how far we are into the post-PDI descent as a percentage
    elapsed_since_pdi = t - pdi_seconds
    descent_progress = min(1.0, elapsed_since_pdi / target_descent_duration)
    
    # More gradual pitch transitions based on progress
    if descent_progress < 0.1:  # Initial post-PDI phase
        return -10 * deg
    elif descent_progress < 0.3:
        return -15 * deg
    elif descent_progress < 0.5:
        return -25 * deg
    elif descent_progress < 0.7:
        return -35 * deg
    elif descent_progress < 0.85:
        return -50 * deg
    elif descent_progress < 0.95:
        return -70 * deg
    else:
        return -85 * deg  # Final approach
    
def descent_throttle_program(t, altitude, velocity):
    """Returns thrust fraction based on time, altitude and velocity"""
    descent_rate = -velocity  # Convert to positive for easier logic
    
    # Pre-PDI phase - minimal thrust for orbital adjustment
    if t < pdi_seconds:
        return 0.05  # Minimal thrust for shallow descent initiation
    
    # Target slower descent times
    target_descent_duration = 12.5 * 60  # 12.5 minutes in seconds
    elapsed_since_pdi = t - pdi_seconds
    
    # Limit throttle to slow down descent
    if altitude > 10000:
        return min(0.5, 0.2 + elapsed_since_pdi/800)  # Gradually increase to 0.5
    elif altitude > 4000:
        return 0.6  # Moderate thrust
    elif altitude > 1000:
        if descent_rate > 15:
            return 0.7  # Slow down if descending too fast
        return 0.55  # Otherwise moderate thrust
    else:
        # Terminal descent - hover longer
        if descent_rate > 5:
            return 0.65  # More thrust to slow down
        else:
            return 0.5  # Very gentle final descent

# Descent Trajectory Simulation
def descent_derivatives(t, state):
    """Calculate state derivatives for lunar descent"""
    r, theta, phi, v, gamma, psi, m = state
    
    # Local gravity
    g = mu / r**2
    
    # Determine thrust
    remaining_propellant = m - (LM_Descent_mstruc + LM_Ascent_m0)
    if t < LM_Descent_tburn and remaining_propellant > 0:
        altitude = r - Re
        # For descent, negative velocity means descending
        descent_rate = -v * np.sin(gamma)
        throttle = descent_throttle_program(t, altitude, descent_rate)
        T = LM_Descent_Thrust * throttle
        mdot = -LM_Descent_mdot * throttle
    else:
        T = 0
        mdot = 0
    
    # Target pitch from guidance (negative for descent)
    gamma_target = descent_pitch_program(t, r - Re)
    
    # Simple guidance
    K_p = 0.1  # Proportional gain
    max_rate = 1.0 * deg  # Max angular rate
    gamma_dot = np.clip(K_p * (gamma_target - gamma), -max_rate, max_rate)
    
    # Position derivatives - for descent gamma is negative, so r_dot is negative
    r_dot = v * np.sin(gamma)
    theta_dot = v * np.cos(gamma) * np.cos(psi) / (r * np.cos(phi))
    phi_dot = v * np.cos(gamma) * np.sin(psi) / r
    

    psi_dot = 0
    
    # Velocity derivative - thrust opposes gravity for controlled descent
    a_thrust = T / m
    a_gravity = -g  # Gravity pulls downward
    
    # For descent: thrust works against gravity, positive thrust slows descent
    v_dot = a_thrust * np.sin(abs(gamma)) + a_gravity * np.sin(gamma)
    
    return [r_dot, theta_dot, phi_dot, v_dot, gamma_dot, psi_dot, mdot]

# Event function for reaching surface
def reach_surface(t, state):
    r, theta, phi, v, gamma, psi, m = state
    return r - Re
reach_surface.terminal = True
reach_surface.direction = -1  # Trigger when crossing from above

# Ascent Stage Guidance
def ascent_pitch_program(t):
    """Returns the target pitch angle at time t during ascent"""
    if t < 10:
        return 90 * deg  # Vertical rise
    elif t < 200:
        # Gradually pitch over
        frac = (t - 10) / 190
        return 90 * deg * (1 - np.sin(frac * np.pi/2))
    else:
        return 0 * deg  # Horizontal flight

def ascent_throttle_program(t, h, v):
    """Returns thrust fraction based on time and state during ascent"""
    if t < LM_Ascent_tburn:
        if h > target_radius - Re - 10000:  # Near target altitude
            alt_error = (target_radius - Re - h) / 10000
            return max(0.6, min(1.0, alt_error + 0.6))
        return 1.0  # Full thrust
    return 0.0  # Engine cutoff

# Ascent Trajectory Simulation
def ascent_derivatives(t, state):
    """Calculate state derivatives for lunar ascent"""
    r, theta, phi, v, gamma, psi, m = state
    
    # Local gravity
    g = mu / r**2
    
    # Determine if engine is burning and remaining propellant
    remaining_propellant = m - (LM_Ascent_mstruc + LM_Ascent_mpl)
    if t < LM_Ascent_tburn and remaining_propellant > 0:
        throttle = ascent_throttle_program(t, r - Re, v)
        T = LM_Ascent_Thrust * throttle
        mdot = -LM_Ascent_mdot * throttle
    else:
        T = 0
        mdot = 0
    
    # Target pitch from guidance
    gamma_target = ascent_pitch_program(t)
    
    # Simple proportional control for pitch
    K_p = 0.1  # Proportional gain
    max_rate = 0.5 * deg  # Maximum pitch rate (deg/s)
    gamma_dot = np.clip(K_p * (gamma_target - gamma), -max_rate, max_rate)
    
    # Position derivatives
    r_dot = v * np.sin(gamma)
    theta_dot = v * np.cos(gamma) * np.cos(psi) / (r * np.cos(phi))
    phi_dot = v * np.cos(gamma) * np.sin(psi) / r
    
    # Calculate CSM position for rendezvous guidance
    # This is simplified - in reality would need more complex rendezvous logic
    if r - Re > 20000:  # Only start rendezvous guidance at higher altitude
        psi_dot = 0  # Maintain heading during initial ascent
    else:
        psi_dot = 0  # Simplified - would need actual rendezvous guidance here
    
    # Velocity derivative
    a_thrust = T / m
    a_gravity = -g
    a_centripetal = v**2 * np.cos(gamma)**2 / r
    
    v_dot = a_thrust + a_gravity * np.sin(gamma) + a_centripetal * np.sin(gamma)
    
    return [r_dot, theta_dot, phi_dot, v_dot, gamma_dot, psi_dot, mdot]

# Event function for reaching target altitude
def reach_target_altitude(t, state):
    r, theta, phi, v, gamma, psi, m = state
    return r - target_radius
reach_target_altitude.terminal = True
reach_target_altitude.direction = 1  # Trigger when crossing from below

# Run the simulations
# 1. CSM orbit - generate positions for the entire mission
mission_start = datetime.datetime(1969, 7, 20, 17, 0, 0)  # Approximate
descent_start_time = datetime.datetime(1969, 7, 20, 19, 8, 0)  # Start of descent at 19:08 UT
pdi_time = datetime.datetime(1969, 7, 20, 20, 5, 0)  # Powered Descent Initiation at 20:05 UT
landing_time = datetime.datetime(1969, 7, 20, 20, 17, 40)  # Actual landing time
takeoff_time = datetime.datetime(1969, 7, 21, 17, 54, 0)
mission_end = datetime.datetime(1969, 7, 21, 21, 0, 0)

total_mission_time = (mission_end - mission_start).total_seconds()
csm_times = np.linspace(0, total_mission_time, 1000)
csm_initial_phase = 0  # Starting position of CSM (45 degrees back from 0)
csm_positions = np.array([csm_orbit(t, csm_initial_phase) for t in csm_times])
csm_x, csm_y, csm_z, csm_phases = csm_positions.T

# Calculate PDI time in seconds from descent start
pdi_seconds = (pdi_time - descent_start_time).total_seconds()
total_descent_time = (landing_time - descent_start_time).total_seconds()

# 2. Descent stage - from CSM orbit to surface
# Initial state: [radius, longitude, latitude, velocity, flight_path_angle, heading, mass]
descent_initial_state = [
    csm_radius,               # Initial radius (CSM orbit)
    launch_longitude + 3.2,   # Initial longitude (farther to the right for starting more on the x+ axis)
    launch_latitude,          # Initial latitude
    csm_velocity,             # Initial velocity (orbital velocity)
    -5 * deg,                 # Initial flight path angle (shallow descent)
    180 * deg,                # Initial heading (toward landing site)
    LM_Descent_m0             # Initial mass (descent + ascent stages)
]

# Update simulation parameters to account for longer descent time
t_max_descent = total_descent_time + 100  # Add margin to the total descent time

print("Simulating descent trajectory...")
descent_sol = solve_ivp(
    descent_derivatives, 
    [0, t_max_descent], 
    descent_initial_state,
    method='RK45',
    events=[reach_surface],
    rtol=1e-6, 
    atol=1e-8
)

descent_t = descent_sol.t
descent_r = descent_sol.y[0]
descent_theta = descent_sol.y[1]
descent_phi = descent_sol.y[2]
descent_v = descent_sol.y[3]
descent_gamma = descent_sol.y[4]
descent_psi = descent_sol.y[5]
descent_m = descent_sol.y[6]

# Calculate PDI index in the solution for analysis
pdi_index = np.argmin(np.abs(descent_t - pdi_seconds))
print(f"Descent complete. Total descent time: {descent_t[-1]/60:.1f} minutes")
print(f"Pre-PDI time: {pdi_seconds/60:.1f} minutes, Post-PDI time: {(descent_t[-1] - pdi_seconds)/60:.1f} minutes")
print(f"Landing coordinates: {descent_phi[-1]/deg:.5f}°N, {descent_theta[-1]/deg:.5f}°E")
print(f"Distance from target: {Re * np.sqrt((descent_phi[-1] - launch_latitude)**2 + (descent_theta[-1] - launch_longitude)**2):.2f} m")
print(f"Final descent velocity: {descent_v[-1]:.2f} m/s")
print(f"Propellant remaining: {descent_m[-1] - (LM_Descent_mstruc + LM_Ascent_m0):.2f} kg")

# 3. Ascent stage - from surface to CSM orbit
ascent_initial_state = [
    Re,                 # Initial radius (surface)
    descent_theta[-1],  # Initial longitude (landing site)
    descent_phi[-1],    # Initial latitude (landing site) 
    0.1,                # Initial velocity (small non-zero)
    90 * deg,           # Initial flight path angle (vertical)
    0.0,                # Initial heading (will adjust for rendezvous)
    LM_Ascent_m0        # Initial mass (ascent stage only)
]

print("Simulating ascent trajectory...")
ascent_sol = solve_ivp(
    ascent_derivatives, 
    [0, t_max_ascent], 
    ascent_initial_state,
    method='RK45',
    events=[reach_target_altitude],
    rtol=1e-6, 
    atol=1e-8
)

ascent_t = ascent_sol.t
ascent_r = ascent_sol.y[0]
ascent_theta = ascent_sol.y[1]
ascent_phi = ascent_sol.y[2]
ascent_v = ascent_sol.y[3]
ascent_gamma = ascent_sol.y[4]
ascent_psi = ascent_sol.y[5]
ascent_m = ascent_sol.y[6]

print(f"Ascent complete.")
print(f"Final altitude: {(ascent_r[-1] - Re)/1000:.2f} km")
print(f"Final velocity: {ascent_v[-1]:.2f} m/s (target: {v_target:.2f} m/s)")
print(f"Propellant remaining: {ascent_m[-1] - (LM_Ascent_mstruc + LM_Ascent_mpl):.2f} kg")

# Calculate actual mission timestamps
surface_start_time = landing_time
ascent_start_time = takeoff_time
ascent_end_time = takeoff_time + datetime.timedelta(seconds=ascent_t[-1])

# Create Cartesian coordinates for visualization
# Convert spherical coordinates to cartesian for visualization
def sphere_to_cart(r, theta, phi):
    x = r * np.cos(phi) * np.cos(theta)
    y = r * np.cos(phi) * np.sin(theta)
    z = r * np.sin(phi)
    return x, y, z

# CSM trajectory
csm_cart = np.array([sphere_to_cart(csm_radius, csm_phases[i], 0) for i in range(len(csm_times))])
csm_x, csm_y, csm_z = csm_cart.T

# Descent trajectory
descent_cart = np.array([sphere_to_cart(descent_r[i], descent_theta[i], descent_phi[i]) for i in range(len(descent_t))])
descent_x, descent_y, descent_z = descent_cart.T

# Ascent trajectory
ascent_cart = np.array([sphere_to_cart(ascent_r[i], ascent_theta[i], ascent_phi[i]) for i in range(len(ascent_t))])
ascent_x, ascent_y, ascent_z = ascent_cart.T

# Visualize the trajectories
plt.figure(figsize=(15, 10))

# 3D plot of all trajectories
ax = plt.subplot(2, 2, 1, projection='3d')
# Draw the Moon
u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
x_moon = Re * np.cos(u) * np.sin(v)
y_moon = Re * np.sin(u) * np.sin(v)
z_moon = Re * np.cos(v)
ax.plot_surface(x_moon, y_moon, z_moon, color='gray', alpha=0.2)

# Plot CSM orbit
ax.plot(csm_x, csm_y, csm_z, 'b-', label='CSM Orbit')

# Plot descent
ax.plot(descent_x, descent_y, descent_z, 'r-', label='Descent')

# Plot ascent
ax.plot(ascent_x, ascent_y, ascent_z, 'g-', label='Ascent')

ax.set_title('Complete Mission Trajectory')
ax.set_xlabel('X (m)')
ax.set_ylabel('Y (m)')
ax.set_zlabel('Z (m)')
ax.legend()

# Plot altitude vs time for descent
plt.subplot(2, 2, 2)
plt.plot(descent_t, descent_r - Re)
plt.axvline(x=pdi_seconds, color='r', linestyle='--', label='PDI')
plt.title('Descent: Altitude vs Time')
plt.xlabel('Time (s)')
plt.ylabel('Altitude (m)')
plt.legend()
plt.grid(True)

# Plot altitude vs time for ascent
plt.subplot(2, 2, 3)
plt.plot(ascent_t, ascent_r - Re)
plt.axhline(y=target_altitude_km*1000, color='r', linestyle='--', label='Target Altitude')
plt.title('Ascent: Altitude vs Time')
plt.xlabel('Time (s)')
plt.ylabel('Altitude (m)')
plt.grid(True)
plt.legend()

# Plot velocity vs time
plt.subplot(2, 2, 4)
plt.plot(descent_t, descent_v, 'r-', label='Descent')
plt.plot(ascent_t, ascent_v, 'g-', label='Ascent')
plt.axhline(y=v_target, color='b', linestyle='--', label='Orbit Velocity')
plt.title('Velocity vs Time')
plt.xlabel('Time (s)')
plt.ylabel('Velocity (m/s)')
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()

# Generate CZML for Cesium visualization
czml = [
    {
        "id": "document",
        "name": "Apollo 11 Moon Mission",
        "version": "1.0",
        "clock": {
            "interval": f"{mission_start.isoformat()}Z/{mission_end.isoformat()}Z",
            "currentTime": f"{mission_start.isoformat()}Z",
            "multiplier": 60,  # Speed up playback
            "range": "LOOP_STOP",
            "step": "SYSTEM_CLOCK_MULTIPLIER"
        }
    },
    # Add the Moon
    {
        "id": "Moon",
        "name": "Moon",
        "position": {
            "cartesian": [0, 0, 0]
        },
        "ellipsoid": {
            "radii": {
                "cartesian": [Re, Re, Re]
            },
            "material": {
                "solidColor": {
                    "color": {
                        "rgba": [200, 200, 200, 255]
                    }
                }
            }
        }
    }
]

# Add CSM trajectory
csm_positions = []
csm_time_increment = total_mission_time / 1000
for i in range(len(csm_times)):
    time_seconds = csm_times[i]
    csm_positions.extend([time_seconds, csm_x[i], csm_y[i], csm_z[i]])

czml.append({
    "id": "CSM",
    "name": "Columbia CSM",
    "availability": f"{mission_start.isoformat()}Z/{mission_end.isoformat()}Z",
    "path": {
        "material": {
            "solidColor": {
                "color": {
                    "rgba": [0, 0, 255, 255]  # Blue
                }
            }
        },
        "width": 2,
        "leadTime": 0,
        "trailTime": csm_period,  # Show one orbit of trail
        "resolution": 120,
        "show": True
    },
    "position": {
        "interpolationAlgorithm": "LAGRANGE",
        "interpolationDegree": 2,
        "epoch": f"{mission_start.isoformat()}Z",
        "cartesian": csm_positions
    },
    "model": {
        "gltf": "/models/csm/csm.gltf",
        "minimumPixelSize": 64,
        "maximumScale": 20000
    },
    "label": {
        "text": "Columbia CSM",
        "font": "11pt Lucida Console",
        "style": "FILL_AND_OUTLINE",
        "outlineWidth": 2,
        "outlineColor": {
            "rgba": [0, 0, 0, 255]
        },
        "horizontalOrigin": "LEFT",
        "verticalOrigin": "TOP",
        "pixelOffset": {
            "cartesian2": [10, 0]
        },
        "fillColor": {
            "rgba": [255, 255, 255, 255]
        },
        "show": True
    }
})

# Add LM Descent trajectory
descent_positions = []
for i in range(len(descent_t)):
    time_seconds = descent_t[i]
    descent_positions.extend([time_seconds, descent_x[i], descent_y[i], descent_z[i]])

czml.append({
    "id": "LM_Descent",
    "name": "Eagle Descent",
    "availability": f"{descent_start_time.isoformat()}Z/{landing_time.isoformat()}Z",
    "path": {
        "material": {
            "solidColor": {
                "color": {
                    "rgba": [255, 0, 0, 255]  # Red
                }
            }
        },
        "width": 3,
        "leadTime": 0,
        "trailTime": 600,  # Show 10 min of trail
        "show": True
    },
    "position": {
        "interpolationAlgorithm": "LAGRANGE",
        "interpolationDegree": 2,
        "epoch": f"{descent_start_time.isoformat()}Z",
        "cartesian": descent_positions
    },
    "model": {
        "gltf": "/models/lm/lunarmodule.gltf",
        "minimumPixelSize": 64,
        "maximumScale": 20000
    },
    "label": {
        "text": "Eagle LM (Descent)",
        "show": True
    }
})

# Add surface stay
landing_site_x, landing_site_y, landing_site_z = sphere_to_cart(Re, descent_theta[-1], descent_phi[-1])

czml.append({
    "id": "LM_Surface",
    "name": "Eagle on Surface",
    "availability": f"{landing_time.isoformat()}Z/{ascent_start_time.isoformat()}Z",
    "position": {
        "cartesian": [landing_site_x, landing_site_y, landing_site_z]
    },
    "model": {
        "gltf": "/models/lm/lunar_lander.gltf",
        "minimumPixelSize": 64,
        "maximumScale": 20000
    },
    "label": {
        "text": "Tranquility Base",
        "show": True
    },
    "point": {
        "color": {
            "rgba": [255, 255, 0, 255]
        },
        "outlineColor": {
            "rgba": [0, 0, 0, 255]
        },
        "outlineWidth": 2,
        "pixelSize": 10,
        "show": True
    }
})

# Add LM Ascent trajectory
ascent_positions = []
for i in range(len(ascent_t)):
    time_seconds = ascent_t[i]
    ascent_positions.extend([time_seconds, ascent_x[i], ascent_y[i], ascent_z[i]])

czml.append({
    "id": "LM_Ascent",
    "name": "Eagle Ascent",
    "availability": f"{ascent_start_time.isoformat()}Z/{ascent_end_time.isoformat()}Z",
    "path": {
        "material": {
            "solidColor": {
                "color": {
                    "rgba": [0, 255, 0, 255]  # Green
                }
            }
        },
        "width": 3,
        "leadTime": 0,
        "trailTime": 600,  # Show 10 min of trail
        "show": True
    },
    "position": {
        "interpolationAlgorithm": "LAGRANGE",
        "interpolationDegree": 2,
        "epoch": f"{ascent_start_time.isoformat()}Z",
        "cartesian": ascent_positions
    },
    "model": {
        "gltf": "/models/lm/lm_ascent.gltf",
        "minimumPixelSize": 64,
        "maximumScale": 20000
    },
    "label": {
        "text": "Eagle LM (Ascent)",
        "show": True
    }
})

# Write CZML to file
czml_file_path = os.path.join(os.path.dirname(__file__), "apollo11_mission.czml")
with open(czml_file_path, "w") as czml_file:
    json.dump(czml, czml_file, indent=2)

print(f"CZML file written to {czml_file_path}")