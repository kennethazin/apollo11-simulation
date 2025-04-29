import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import solve_ivp
import os
import json  # Add import for JSON to create CZML

# rocket inputs
# modelling the saturn V 

# Constants
omega = 7.2921159e-5  # rad/s Earth's angular velocity
Re = 6371000  # m Earth's radius
g0 = 9.81  # m/s² standard gravitational acceleration
rho0 = 1.225  # kg/m³ sea-level air density
hscale = 11100  # m scale height for Earth's atmosphere
deg = np.pi / 180  # Conversion factor from degrees to radians https://stackoverflow.com/questions/10140029/convert-latitude-longitude-in-degree-radians

# Add launch pad delay (4 minutes 15 seconds = 255 seconds)
launch_delay = 255  # seconds before rocket starts to move

# Rocket Geometry
diam = 10.0584  # m (33 ft converted to meters)
A = np.pi / 4 * (diam)**2  # m² frontal area
CD = 0.515  # Drag coefficient https://space.stackexchange.com/questions/12649/how-can-i-estimate-the-coefficient-of-drag-on-a-saturn-v-rocket-a-simulator-or

# Stage 1
mprop = 2145000  # kg propellant mass
mstruc = 131000  # kg structural mass
mpl = 45400  # kg payload mass
tburn1 = 164  # s burn time (2 minutes 44 seconds - matches 13:32:00 to 13:34:44)
Thrust = 35100000  # N thrust
m_dot = mprop / tburn1  # kg/s propellant mass flow rate
tcoast = 0 # (seconds)
 
# Stage 2
diam2 = 10.0584  # m
mstruc2 = 40100  # kg structural mass
mprop2 = 456100  # kg propellant mass
tburn2 = 391  # s burn time (6 minutes 31 seconds - matches 13:34:44 to 13:41:15)
Thrusts2 = 5140000  # N thrust
m_dot2 = mprop2 / tburn2  # kg/s propellant mass flow rate
m0s2 = mstruc2 + mprop2 + mpl  # total mass at the start of stage 2
tcoast2 = 10 # (seconds) - Second stage ignition followed shortly after separation

# Stage 3
diam3 = 6.604  # m diameter of stage 3 (21.7 ft)
mstruc3 = 10900  # kg structural mass
mprop3 = 119000  # kg propellant mass kg http://www.apolloexplorer.co.uk/pdf/saturnv/Third%20Stage.pdf
tburn3_1 = 150  # s first burn duration (2 minutes 30 seconds - matches 13:41:15 to 13:43:45)
tburn3_2 = 357  # s second burn duration (5 minutes 57 seconds - matches 16:16:16 to 16:22:13)
tcoast3 = 9151 # s coasting time between burns (2 hours 32 minutes 31 seconds - matches 13:43:45 to 16:16:16)
Thrust3 = 1000000 # N thrust for stage 3 (225,000 lbf)
m_dot3 = mprop3 / (tburn3_1 + tburn3_2) # kg/s propellant mass flow rate for stage 3 
m0s3 = mstruc3 + mprop3 + mpl  # total mass at the start of stage 3

# Total Initial Mass
m0 = mprop + mprop2 + mstruc + mstruc2 + mprop3 + mstruc3 + mpl # total lift-off mass (kg)

# Pitchover and Simulation Parameters
hturn = 100  # m reduced pitchover height to start turning earlier
t_max = 12000 + launch_delay  # s simulation duration - enough time to reach orbit (including delay)
v0 = 0  # m/s initial velocity
psi0 = 89.5 * deg  # rad initial flight path angle - almost vertical at launch
theta0 = 0  # rad initial downrange angle
h0 = 43 # m initial altitude

# Kennedy Space Center Launch Pad 39A coordinates https://www.nasa.gov/wp-content/uploads/static/history/afj/ap10fj/pdf/as-505-postflight-trajectory.pdf
latitude_39a = (28.44685) * deg  # radians (slightly more up)
longitude_39a = (-80.6041) * deg  # radians (slightly more left)
altitude_39a = 73  # meters

# Convert to Cartesian coordinates
R_39a = Re + altitude_39a  # Earth's radius + altitude of the launch pad
x_39a = R_39a * np.cos(latitude_39a) * np.cos(longitude_39a)
y_39a = R_39a * np.cos(latitude_39a) * np.sin(longitude_39a)
z_39a = R_39a * np.sin(latitude_39a)

# Define TLI end time based on actual mission timeline with added delay
# Total time from liftoff: 2 hours 50 minutes 13 seconds (10213 seconds) + launch delay
tli_end_time = tburn1 + tburn2 + tcoast + tburn3_1 + tcoast3 + tburn3_2 + launch_delay

# Target altitudes for each stage (in meters)
target_altitude_s1 = 68000  # 68 km after stage 1
target_altitude_s2 = 175000  # 175 km after stage 2
target_altitude_orbit = 160000  # 160 km orbital altitude
target_velocity_tli = 10.8  # km/s TLI target velocity (escape velocity)

def gravity_turn_program(t, h, v):
    """
    More sophisticated gravity turn program based on time and altitude
    Returns the target flight path angle in radians
    
    Note: t is the simulation time which includes the launch delay
    """
    # If we're in the delay period, maintain vertical orientation
    if t < launch_delay:
        return 90 * deg
        
    # Adjust t to be time since actual launch
    t_since_launch = t - launch_delay
    
    if h <= hturn:
        # Initial vertical climb
        return 89.5 * deg
    elif t_since_launch < tburn1:
        # First stage - gradually pitch over from 90° to about 45° by end of S-IC
        # Linear interpolation between initial pitch and target pitch
        t_frac = (t_since_launch - (hturn / v0 if v0 > 0 else 10)) / tburn1  # normalized time after pitchover
        return max((89.5 - 44.5 * t_frac) * deg, 45 * deg)
    elif t_since_launch < tburn1 + tburn2:
        # Second stage - continue pitching over to near horizontal
        t_frac = (t_since_launch - tburn1) / tburn2  # normalized time in S-II
        # More gradual transition to prevent diving - minimum angle of 5 degrees
        return max((45 - 35 * t_frac) * deg, 5 * deg)
    elif t_since_launch < tburn1 + tburn2 + tburn3_1:
        # First S-IVB burn - approach orbital insertion
        t_frac = (t_since_launch - tburn1 - tburn2) / tburn3_1  # normalized time in S-IVB
        # Gradual transition to horizontal - minimum angle of 0 degrees (never negative)
        return max((5 - 5 * t_frac) * deg, 0 * deg)
    elif t_since_launch < tburn1 + tburn2 + tburn3_1 + tcoast3:
        # Earth Parking Orbit coast phase - maintain 0 degrees for horizontal flight
        return 0 * deg
    elif t_since_launch < tburn1 + tburn2 + tburn3_1 + tcoast3 + tburn3_2:
        # TLI burn - gradually adjust to escape trajectory
        t_frac = (t_since_launch - (tburn1 + tburn2 + tburn3_1 + tcoast3)) / tburn3_2
        # Start at 0 and gradually increase to ~10 degrees for TLI escape trajectory
        return min(10 * t_frac * deg, 10 * deg)
    else:
        # Post-TLI - maintain escape trajectory toward Moon
        return 2 * deg  # TLI angle toward Moon

def derivatives(t, y):
    v = y[0]  # m/s
    psi = y[1]  # radians - flight path angle
    theta = y[2]  # radians - downrange angle
    h = y[3]  # m - altitude
    
    # If we're still in the delay period, keep the rocket stationary
    if t < launch_delay:
        return [0, 0, 0, 0]
    
    # Limit the altitude for numerical stability
    h = min(h, 1000000)  # Limit to 1000 km to prevent numerical issues
    
    # Calculate radius from Earth's center
    r = Re + h
    
    # Calculate gravity with inverse square law
    g = g0 * (Re / r) ** 2
    
    # Calculate atmospheric density (exponential model)
    rho = rho0 * np.exp(-h / hscale) if h < 100000 else 0  # No significant atmosphere above 100km
    
    # Calculate drag
    D = 0.5 * rho * v**2 * A * CD if v > 0 else 0
    
    # Adjust time to be time since launch
    t_since_launch = t - launch_delay
    
    # Calculate mass and thrust for each stage - using time since actual launch
    if t_since_launch < tburn1:
        m = m0 - m_dot * t_since_launch
        T = Thrust
    elif t_since_launch < tburn1 + tburn2:
        m = m0s2 - m_dot2 * (t_since_launch - tburn1)
        T = Thrusts2
    elif t_since_launch < tburn1 + tburn2 + tcoast:
        m = m0s2 - m_dot2 * (tburn2)
        T = 0
    elif t_since_launch < tburn1 + tburn2 + tcoast + tburn3_1:
        m = m0s3 - m_dot3 * (t_since_launch - tburn1 - tburn2 - tcoast)
        T = Thrust3
    elif t_since_launch < tburn1 + tburn2 + tcoast + tburn3_1 + tcoast3:
        m = m0s3 - m_dot3 * tburn3_1
        T = 0
    elif t_since_launch < tburn1 + tburn2 + tcoast + tburn3_1 + tcoast3 + tburn3_2:
        m = m0s3 - m_dot3 * (tburn3_1 + (t_since_launch - tburn1 - tburn2 - tcoast - tburn3_1 - tcoast3))
        T = Thrust3
    else:
        m = mstruc3 + mpl
        T = 0
    
    # Get target flight path angle from gravity turn program
    target_psi = gravity_turn_program(t, h, v)
    
    # Apply steering to gradually adjust flight path angle
    # More gentle steering rate based on altitude
    steering_factor = 0.02 if h < 50000 else 0.01  # Slower steering at higher altitudes
    psi_error = target_psi - psi
    psi_rate = steering_factor * psi_error  # Smoother control with reduced rate
    
    # Prevent negative flight path angles during critical ascent phases
    if h < 150000 and psi < 0 and psi_rate < 0:
        psi_rate = max(psi_rate, 0.01)  # Force gentle upward correction if diving
    
    # Calculate force components
    # Thrust along velocity vector
    thrust_force = T
    
    # Gravity force (always points down)
    gravity_force = m * g
    
    # Calculate accelerations
    if t_since_launch < tburn1 + tburn2 + tcoast + tburn3_1 + tcoast3:  # Before TLI burn
        if h < 160000:  # During atmospheric ascent and initial orbital insertion
            # Standard rocket equations with gravity turn
            v_dot = (thrust_force - D) / m - g * np.sin(psi)  # Corrected gravity component
            h_dot = v * np.sin(psi)
            theta_dot = v * np.cos(psi) / (Re + h) 
            psi_dot = psi_rate
        else:
            # Orbital mechanics for Earth parking orbit
            orbital_velocity = np.sqrt(g0 * Re**2 / r)
            v_target = orbital_velocity
            v_error = v_target - v
            v_dot = 0.1 * v_error  # Gentle adjustment toward orbital velocity
            h_dot = v * np.sin(psi)
            theta_dot = v * np.cos(psi) / r  # Angular velocity in orbit
            psi_dot = psi_rate  # Use controlled steering during orbit
    else:  # During and after TLI burn
        # TLI and beyond - escape trajectory calculations
        if t_since_launch < tburn1 + tburn2 + tcoast + tburn3_1 + tcoast3 + tburn3_2:
            # During TLI burn - accelerate and change trajectory
            v_dot = thrust_force / m - g * np.sin(psi)  # Accelerate to escape velocity
            h_dot = v * np.sin(psi)
            theta_dot = v * np.cos(psi) / (Re + h)
            psi_dot = psi_rate  # Follow the gravity turn program for TLI
        else:
            # After TLI burn - coasting on escape trajectory
            v_dot = -g * np.sin(psi)  # Only gravity affects velocity now
            h_dot = v * np.sin(psi)
            theta_dot = v * np.cos(psi) / (Re + h)
            psi_dot = -g * np.cos(psi) / v + v * np.cos(psi) / (Re + h)  # Natural trajectory
    
    # Additional check to stabilize at orbital altitude during parking orbit
    if t_since_launch < tburn1 + tburn2 + tcoast + tburn3_1 + tcoast3 and h > target_altitude_orbit and h_dot > 0 and h_dot < 10:
        h_dot = 0  # Stabilize at target orbital altitude during parking orbit only
    
    return [v_dot, psi_dot, theta_dot, h_dot]

# Run the simulation
sol = solve_ivp(derivatives, [0, t_max], [v0, psi0, theta0, h0], rtol=1e-6, atol=1e-6)

psi = sol.y[1] # rad flight path angle
psideg = psi/deg
theta = sol.y[2] # rad downrange angle
dr = theta*Re / 1000 # km downrange distance
h = sol.y[3]/1000 # km altitude
htot = h + Re/1000 # km total
t = sol.t
vrel = sol.y[0]/1000 # % km/s velocity WITHOUT rotation of earth
vabs = sol.y[0] + omega * (Re + h*1000) * np.cos(latitude_39a)

print(sol)

Rearraytheta = np.linspace(0, 2*np.pi,100)
Rearray = np.full((100,1), Re/1000)

# Define launch time for CZML - this will be the actual start time in the visualization
launch_datetime = "1969-07-16T13:27:45Z"  # 4:15 before 13:32:00

# Generate CZML data
czml = [
    {
        "id": "document",
        "name": "Saturn V Trajectory",
        "version": "1.0",
        "clock": {
            "interval": f"{launch_datetime}/1969-07-16T{13 + int(t_max) // 3600:02}:{(32 + (int(t_max) % 3600) // 60) % 60:02}:{(int(t_max) % 60):02}Z",
            "currentTime": launch_datetime,
            "range": "LOOP_STOP",
            "step": "SYSTEM_CLOCK_MULTIPLIER"
        }
    }
]

# Add trajectory path - include stationary period
positions = []
epoch = launch_datetime  # Start at the launch pad time
for i in range(len(t)):
    r = Re + h[i] * 1000 + altitude_39a + 2130  # Radius from Earth's center + manual adjustment 
    x = r * np.cos(latitude_39a) * np.cos(longitude_39a + theta[i])  # X in meters
    y = r * np.cos(latitude_39a) * np.sin(longitude_39a + theta[i])  # Y in meters
    z = r * np.sin(latitude_39a)  # Z in meters
    positions.extend([t[i], x, y, z])  # Time, X, Y, Z

# Calculate the liftoff time as datetime string
# Create time formatting function to handle the conversion
def format_mission_time(base_time, seconds_to_add):
    # Parse base time hours and minutes
    base_hours = int(base_time.split('T')[1].split(':')[0])
    base_minutes = int(base_time.split('T')[1].split(':')[1])
    base_seconds = int(base_time.split('T')[1].split(':')[2].replace('Z', ''))
    
    # Calculate total seconds
    total_seconds = base_seconds + seconds_to_add
    
    # Calculate new hours, minutes, seconds
    new_seconds = total_seconds % 60
    total_minutes = base_minutes + (total_seconds // 60)
    new_minutes = total_minutes % 60
    total_hours = base_hours + (total_minutes // 60)
    new_hours = total_hours % 24
    
    # Format and return
    return f"1969-07-16T{new_hours:02}:{new_minutes:02}:{new_seconds:02}Z"

# Calculate actual liftoff time (after delay)
liftoff_time = format_mission_time(launch_datetime, launch_delay)

# Add Saturn V entity
czml.append({
    "id": "SaturnV",
    "name": "Saturn V",
    "availability": f"{launch_datetime}/{format_mission_time(launch_datetime, tli_end_time)}",
    "model": {
        "gltf": "models/saturnv/saturnv.gltf",  # Correct model path (no leading slash)
        "minimumPixelSize": 128,
        "maximumScale": 20000
    },
    "position": {
        "interpolationAlgorithm": "LAGRANGE",
        "interpolationDegree": 2,
        "epoch": epoch,
        "cartesian": positions
    },
    "orientation": {
        "interpolationAlgorithm": "LINEAR",
        "interpolationDegree": 1,
        "epoch": epoch,
        # Start with upright orientation during pre-launch, then switch to velocity reference
        "unitQuaternion": [
            0.0, 0, 0, 0, 1,  # At t=0, upright orientation (aligned with launch site normal vector)
            launch_delay, 0, 0, 0, 1,  # Maintain upright until launch
        ],
        "velocityReference": "#position",  # After launch, orient according to velocity
        "referenceFrame": "INERTIAL"
    },
    "path": {
        "leadTime": 0,
        "trailTime": 86400,
        "material": {
            "solidColor": {
                "color": {
                    "rgba": [255, 0, 0, 255]  # Red color for Saturn V path
                }
            }
        },
        "width": 2,
        "show": True
    }
})

# Keep only one Post-TLI entity (removing duplicate)
czml.append({
    "id": "Post-TLI",
    "name": "CSM-LM",
    "availability": f"{format_mission_time(launch_datetime, tli_end_time)}/{format_mission_time(launch_datetime, t_max)}",
    "model": {
        "gltf": "models/csm_lm/csmlm.gltf",  # Correct model path (no leading slash)
        "minimumPixelSize": 64,
        "maximumScale": 20000
    },
    "position": {
        "interpolationAlgorithm": "LAGRANGE",
        "interpolationDegree": 2,
        "epoch": epoch,
        "cartesian": positions  # Use the same position data
    },
    "orientation": {
        "velocityReference": "#position"  # Orient along velocity vector
    },
    "path": {
        "leadTime": 0,
        "trailTime": 86400,
        "material": {
            "solidColor": {
                "color": {
                    "rgba": [0, 255, 0, 255]  # Green color for LM path
                }
            }
        },
        "width": 2,
        "show": True
    }
})

# Add stage information with adjusted times to include delay
stages = [
    {"id": "prelaunch", "name": "Pre-Launch", "start": 0, "end": launch_delay},
    {"id": "stage1", "name": "Stage 1", "start": launch_delay, "end": launch_delay + tburn1},
    {"id": "stage2", "name": "Stage 2", "start": launch_delay + tburn1, "end": launch_delay + tburn1 + tburn2},
    {"id": "stage3_burn1", "name": "Stage 3 Burn 1", "start": launch_delay + tburn1 + tburn2 + tcoast, "end": launch_delay + tburn1 + tburn2 + tcoast + tburn3_1},
    {"id": "stage3_coast", "name": "Stage 3 Coast", "start": launch_delay + tburn1 + tburn2 + tcoast + tburn3_1, "end": launch_delay + tburn1 + tburn2 + tcoast + tburn3_1 + tcoast3},
    {"id": "stage3_burn2", "name": "Stage 3 Burn 2", "start": launch_delay + tburn1 + tburn2 + tcoast + tburn3_1 + tcoast3, "end": launch_delay + tburn1 + tburn2 + tcoast + tburn3_1 + tcoast3 + tburn3_2}
]

for stage in stages:
    stage_start_time = format_mission_time(launch_datetime, stage["start"])
    stage_end_time = format_mission_time(launch_datetime, stage["end"])
    
    czml.append({
        "id": stage["id"],
        "name": stage["name"],
        "availability": f"{stage_start_time}/{stage_end_time}",
        "description": f"{stage['name']} active from {stage['start']}s to {stage['end']}s"
    })

# Write CZML to file
czml_file_path = os.path.join(os.path.dirname(__file__), "saturn_v_trajectory_with_delay.czml")
with open(czml_file_path, "w") as czml_file:
    json.dump(czml, czml_file, indent=2)

print(f"CZML file written to {czml_file_path}")

# Print simulation results
print("\n--- Saturn V Launch Simulation Results ---")
print(f"Pre-launch delay: {launch_delay} seconds (4 minutes 15 seconds)")
print(f"Launch time: {liftoff_time}")
print(f"Total simulation time: {t[-1]:.1f} seconds")

# Find indexes for key points
launch_idx = np.argmax(t > launch_delay) if np.any(t > launch_delay) else 0
s1_end_idx = np.argmax(t > launch_delay + tburn1) if np.any(t > launch_delay + tburn1) else -1
s2_end_idx = np.argmax(t > launch_delay + tburn1 + tburn2) if np.any(t > launch_delay + tburn1 + tburn2) else -1
orbit_idx = np.argmax(t > launch_delay + tburn1 + tburn2 + tburn3_1) if np.any(t > launch_delay + tburn1 + tburn2 + tburn3_1) else -1

# Print stage-specific data
print(f"Initial launch pad altitude: {h[0]:.2f} km")

if s1_end_idx > 0:
    print(f"Altitude after Stage 1: {h[s1_end_idx]:.2f} km")
    print(f"Velocity after Stage 1: {vrel[s1_end_idx]:.2f} km/s")

if s2_end_idx > 0:
    print(f"Altitude after Stage 2: {h[s2_end_idx]:.2f} km")
    print(f"Velocity after Stage 2: {vrel[s2_end_idx]:.2f} km/s")

if orbit_idx > 0:
    print(f"Orbital Altitude: {h[orbit_idx]:.2f} km")
    print(f"Orbital Velocity: {vrel[orbit_idx]:.2f} km/s")

print(f"Final Altitude: {h[-1]:.2f} km")
print(f"Final Velocity (Relative): {vrel[-1]:.4f} km/s")
print(f"Final Velocity (Absolute): {vabs[-1]:.4f} km/s")
print(f"Final Flight Path Angle: {psideg[-1]:.2f} degrees")
print(f"Downrange Distance: {dr[-1]:.2f} km")

# Define stage colors for plotting
stage_colors = ['darkblue', 'blue', 'green', 'orange', 'purple', 'red', 'cyan']

# Create time values that show minutes since simulation start
minutes_elapsed = t / 60

# Plotting the results
plt.figure(figsize=(12, 10))

# Height vs Time (Top Left)
plt.subplot(3, 2, 1)
plt.plot(minutes_elapsed, h, label="Trajectory")
for i, stage in enumerate(stages):
    plt.axvline(stage["start"]/60, color=stage_colors[i], linestyle="--", label=f"{stage['name']} Start")
    plt.axvline(stage["end"]/60, color=stage_colors[i], linestyle=":", label=f"{stage['name']} End")
plt.title('Altitude vs Time')
plt.xlabel('Time (minutes)')
plt.ylabel('Altitude (km)')
plt.grid(True)

# Velocity vs Time (Middle Left)
plt.subplot(3, 2, 3)
plt.plot(minutes_elapsed, vabs, label="Velocity")
for i, stage in enumerate(stages):
    plt.axvline(stage["start"]/60, color=stage_colors[i], linestyle="--")
    plt.axvline(stage["end"]/60, color=stage_colors[i], linestyle=":")
plt.title('Absolute Velocity vs Time')
plt.xlabel('Time (minutes)')
plt.ylabel('Velocity (km/s)')
plt.grid(True)

# Flight Path Angle vs Time (Bottom Left)
plt.subplot(3, 2, 5)
plt.plot(minutes_elapsed, psideg, label="Flight Path Angle")
for i, stage in enumerate(stages):
    plt.axvline(stage["start"]/60, color=stage_colors[i], linestyle="--")
    plt.axvline(stage["end"]/60, color=stage_colors[i], linestyle=":")
plt.title('Flight Path Angle vs Time')
plt.xlabel('Time (minutes)')
plt.ylabel('Flight Path Angle (deg)')
plt.grid(True)

# Polar Trajectory Plot (Top Right)
ax_polar = plt.subplot(3, 2, 2, projection='polar')

# Plot trajectory with different colors for each stage
stage_times = [0] + [stage["end"] for stage in stages]

for i in range(len(stage_times) - 1):
    mask = (t >= stage_times[i]) & (t < stage_times[i + 1])
    ax_polar.plot(theta[mask], htot[mask], color=stage_colors[i], linewidth=2, label=f'{stages[i]["name"]}')

ax_polar.plot(Rearraytheta, Rearray, label='Earth', color='black', linewidth=1.5)  # Earth circle
ax_polar.set_title('Polar Trajectory (Distance vs Angle)')
ax_polar.set_rticks([2000, 4000, 10000])  # Example ticks
ax_polar.set_rlabel_position(-22.5)  # Move radial labels away from plotted line
ax_polar.grid(True)

# Downrange Distance vs Time (Middle Right)
plt.subplot(3, 2, 4)
plt.plot(minutes_elapsed, dr, label="Downrange Distance")
for i, stage in enumerate(stages):
    plt.axvline(stage["start"]/60, color=stage_colors[i], linestyle="--")
    plt.axvline(stage["end"]/60, color=stage_colors[i], linestyle=":")
plt.title('Downrange Distance vs Time')
plt.xlabel('Time (minutes)')
plt.ylabel('Downrange Distance (km)')
plt.grid(True)

# Height vs Downrange Distance (Bottom Right)
plt.subplot(3, 2, 6)
plt.plot(dr, h, label="Trajectory")
# No need for vertical lines on this plot as it's a 2D trajectory

plt.title('Trajectory (Altitude vs Downrange Distance)')
plt.xlabel('Downrange Distance (km)')
plt.ylabel('Altitude (km)')
plt.grid(True)
plt.axis('equal')  # Optional: makes axes scale equally

# Add a single legend for all plots
handles, labels = [], []
for i, stage in enumerate(stages):
    handles.append(plt.Line2D([0], [0], color=stage_colors[i], linestyle="-", label=f"{stage['name']}"))
handles.append(plt.Line2D([0], [0], color='black', linewidth=1.5, label='Earth'))
plt.figlegend(handles=handles, loc='lower center', ncol=4, fontsize="small", frameon=False)

plt.tight_layout(rect=[0, 0.05, 1, 1])  # Adjust layout to fit legend
plt.show()