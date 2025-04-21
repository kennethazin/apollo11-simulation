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

# Rocket Geometry
diam = 10.0584  # m (33 ft converted to meters)
A = np.pi / 4 * (diam)**2  # m² frontal area
CD = 0.515  # Drag coefficient https://space.stackexchange.com/questions/12649/how-can-i-estimate-the-coefficient-of-drag-on-a-saturn-v-rocket-a-simulator-or

# Stage 1
mprop = 2077000  # kg propellant mass
mstruc = 137000  # kg structural mass
mpl = 43500  # kg payload mass
tburn1 = 168  # s burn time
Thrust = 34500000  # N thrust
m_dot = mprop / tburn1  # kg/s propellant mass flow rate
tcoast = 0 # (seconds)
 
# Stage 2
diam2 = 10.0584  # m
mstruc2 = 36000  # kg structural mass
mprop2 = 444000  # kg propellant mass
tburn2 = 366  # s burn time
Thrusts2 = 4400000  # N thrust
m_dot2 = mprop2 / tburn2  # kg/s propellant mass flow rate
m0s2 = mstruc2 + mprop2 + mpl  # total mass at the start of stage 2
tcoast2 = 2000 # (seconds) - Second stage ignition followed shortly after separation

# Stage 3
diam3 = 6.604  # m diameter of stage 3 (21.7 ft)
mstruc3 = 10000  # kg structural mass
mprop3 = 108000  # kg propellant mass
tburn3_1 = 144  # s first burn duration
tburn3_2 = 336  # s second burn duration
tcoast3 = 12000 # s coasting time between burns
Thrust3 = 1003345 # N thrust for stage 3 (225,000 lbf)
m_dot3 = mprop3 / (tburn3_1 + tburn3_2) # kg/s propellant mass flow rate for stage 3 
m0s3 = mstruc3 + mprop3 + mpl  # total mass at the start of stage 3

# Total Initial Mass
m0 = mprop + mprop2 + mstruc + mstruc2 + mprop3 + mstruc3 + mpl # total lift-off mass (kg)


# Pitchover and Simulation Parameters
hturn = 130  # m pitchover height
t_max = 20000  # s simulation duration
v0 = 0  # m/s initial velocity
psi0 = 0.028 * deg  # rad initial flight path angle
theta0 = 0  # rad initial downrange angle
h0 = 0  # m initial altitude

def derivatives(t,y):
    v = y[0] # m/s
    psi = y[1] # radians
    theta = y[2]
    h = y[3]
    # determine gravity and drag
    g = g0 / (1 + h / Re) ** 2
    rho = rho0 * np.exp(-h / hscale)
    D = 1 / 2 * rho * v**2 * A * CD


    # print('h', h)  
    # print('D, D)
    # if statements to determine the thrust and mass
    # update thrust and mass based on if vehicle is still burning
    if t < tburn1:
        m = m0 - m_dot*t
        T = Thrust
    elif t < tburn1 + tburn2: # after stage 1 burn, start burning stage 2
        m = m0s2 - m_dot2 * (t-tburn1) # set mass of vehicle, subtracting out original burn time
        T = Thrusts2 # set thrust to stage 2 thrust
    elif t < tburn1 + tburn2 + tcoast: # coasting stage
        m = m0s2 - m_dot2 * (tburn2) # spacecraft mass after full second burn
        T = 0 # coasting, so thrust is 0
    elif t < tburn1 + tburn2 + tcoast + tburn3_1:  # First burn of stage 3
        m = m0s3 - m_dot3 * (t - tburn1 - tburn2 - tcoast)
        T = Thrust3
    elif t < tburn1 + tburn2 + tcoast + tburn3_1 + tcoast3:  # Coasting between stage 3 burns
        m = m0s3 - m_dot3 * tburn3_1  # Mass after first stage 3 burn
        T = 0  # Coas ting, so thrust is 0
    elif t < tburn1 + tburn2 + tcoast + tburn3_1 + tcoast3 + tburn3_2:  # Second burn of stage 3
        m = m0s3 - m_dot3 * (t - tburn1 - tburn2 - tcoast - tburn3_1 - tcoast3)
        T = Thrust3
    else:
        m = mstruc3 + mpl # final spacecraft mass // is it this? m0s2 - mprop3 
        T = 0 # no longer burning

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

sol = solve_ivp(derivatives, [0, t_max], [v0,psi0,theta0,h0], max_step=1)

vrel = sol.y[0]/1000 # % km/s velocity WITHOUT rotation of earth
vabs = vrel+Re*omega / 1000
psi = sol.y[1] # rad flight path angle
psideg = psi/deg
theta = sol.y[2] # rad downrange angle
dr = theta*Re / 1000 # km downrange distance
h =  sol.y[3]/1000 # km altitude
htot = h + Re/1000 # km total
t = sol.t

print(sol)

Rearraytheta = np.linspace(0, 2*np.pi,100)
Rearray = np.full((100,1), Re/1000)

# Kennedy Space Center Launch Pad 39A coordinates https://www.nasa.gov/wp-content/uploads/static/history/afj/ap10fj/pdf/as-505-postflight-trajectory.pdf
latitude_39a = (28.608) * deg  # radians (slightly more up)
longitude_39a = (-80.604) * deg  # radians (slightly more left)
altitude_39a = 64.1  # meters

# Convert to Cartesian coordinates
R_39a = Re + altitude_39a  # Earth's radius + altitude of the launch pad
x_39a = R_39a * np.cos(latitude_39a) * np.cos(longitude_39a)
y_39a = R_39a * np.cos(latitude_39a) * np.sin(longitude_39a)
z_39a = R_39a * np.sin(latitude_39a)

# Define TLI end time
tli_end_time = tburn1 + tburn2 + tcoast + tburn3_1 + tcoast3 + tburn3_2

# Generate CZML data
czml = [
    {
        "id": "document",
        "name": "Saturn V Trajectory",
        "version": "1.0",
        "clock": {
            "interval": f"1969-07-16T13:32:00Z/1969-07-16T{13 + int(t_max) // 3600:02}:{(32 + (int(t_max) % 3600) // 60) % 60:02}:{(int(t_max) % 60):02}Z",
            "currentTime": "1969-07-16T13:32:00Z",
            "range": "LOOP_STOP",
            "step": "SYSTEM_CLOCK_MULTIPLIER"
        }
    }
]

# Add trajectory path
positions = []
epoch = "1969-07-16T13:32:00Z"
for i in range(len(t)):
    r = Re + h[i] * 1000 + altitude_39a + 2130 # Radius from Earth's center + manual adjustment 
    x = r * np.cos(latitude_39a) * np.cos(longitude_39a + theta[i])  # X in meters
    y = r * np.cos(latitude_39a) * np.sin(longitude_39a + theta[i])  # Y in meters
    z = r * np.sin(latitude_39a)  # Z in meters
    positions.extend([t[i], x, y, z])  # Time, X, Y, Z

czml.append({
    "id": "SaturnV",
    "availability": f"1969-07-16T13:32:00Z/1969-07-16T{13 + int(tli_end_time) // 3600:02}:{(32 + (int(tli_end_time) % 3600) // 60) % 60:02}:{(int(tli_end_time) % 60):02}Z",
    "path": {
        "leadTime": 0,
        "material": {
            "solidColor": {
                "color": {
                    "rgba": [255, 0, 0, 255]  # Red color
                }
            }
        },
        "width": 2,
        "show": True
    },
    "position": {
        "interpolationAlgorithm": "LINEAR",
        "epoch": epoch,
        "cartesian": positions
    },
    "model": {
        "gltf": "/models/saturnv/saturnv.gltf",
        "minimumPixelSize": 64,
        "maximumScale": 20000
    }
})

# Add stage information
stages = [
    {"id": "stage1", "name": "Stage 1", "start": 0, "end": tburn1},
    {"id": "stage2", "name": "Stage 2", "start": tburn1, "end": tburn1 + tburn2},
    {"id": "stage3_burn1", "name": "Stage 3 Burn 1", "start": tburn1 + tburn2 + tcoast, "end": tburn1 + tburn2 + tcoast + tburn3_1},
    {"id": "stage3_coast", "name": "Stage 3 Coast", "start": tburn1 + tburn2 + tcoast + tburn3_1, "end": tburn1 + tburn2 + tcoast + tburn3_1 + tcoast3},
    {"id": "stage3_burn2", "name": "Stage 3 Burn 2", "start": tburn1 + tburn2 + tcoast + tburn3_1 + tcoast3, "end": tburn1 + tburn2 + tcoast + tburn3_1 + tcoast3 + tburn3_2}
]

for stage in stages:
    czml.append({
        "id": stage["id"],
        "name": stage["name"],
        "availability": f"1969-07-16T{13 + int(stage['start']) // 3600:02}:{(32 + (int(stage['start']) % 3600) // 60) % 60:02}:{(int(stage['start']) % 60):02}Z/1969-07-16T{13 + int(stage['end']) // 3600:02}:{(32 + (int(stage['end']) % 3600) // 60) % 60:02}:{(int(stage['end']) % 60):02}Z",
        "description": f"{stage['name']} active from {stage['start']}s to {stage['end']}s"
    })
    
# Add a new model after TLI burn
czml.append({
    "id": "Post-TLI",
    "availability": f"1969-07-16T{13 + int(tli_end_time) // 3600:02}:{(32 + (int(tli_end_time) % 3600) // 60) % 60:02}:{(int(tli_end_time) % 60):02}Z/1969-07-16T{13 + int(t_max) // 3600:02}:{(32 + (int(t_max) % 3600) // 60) % 60:02}:{(int(t_max) % 60):02}Z",
    "model": {
        "gltf": "/models/csm_lm/csmlm.gltf",  # Path to the new model
        "minimumPixelSize": 64,
        "maximumScale": 20000
    },
    "position": {
        "interpolationAlgorithm": "LINEAR",
        "epoch": epoch,
        "cartesian": positions # Use the same position data
    },
    "path": { # Define the path for the Post-TLI entity
        "leadTime": 0,
        "trailTime": 86400, # Show path for a day or adjust as needed
        "material": {
            "solidColor": {
                "color": {
                    "rgba": [0, 255, 0, 255]  # Green color for LM path
                }
            }
        },
        "width": 2,
        "show": True # Initially show the path when the entity is available
    }
})

# Write CZML to file
czml_file_path = os.path.join(os.path.dirname(__file__), "saturn_v_trajectory_orientation.czml")
with open(czml_file_path, "w") as czml_file:
    json.dump(czml, czml_file, indent=2)

print(f"CZML file written to {czml_file_path}")

# Plotting the results
plt.figure(figsize=(12, 10))

# Height vs Time (Top Left)
plt.subplot(3, 2, 1)
plt.plot(t, h)
plt.title('Altitude vs Time')
plt.xlabel('Time (s)')
plt.ylabel('Altitude (km)')
plt.grid(True)

# Velocity vs Time (Middle Left)
plt.subplot(3, 2, 3)
plt.plot(t, vabs)
plt.title('Absolute Velocity vs Time')
plt.xlabel('Time (s)')
plt.ylabel('Velocity (km/s)')
plt.grid(True)

# Flight Path Angle vs Time (Bottom Left)
plt.subplot(3, 2, 5)
plt.plot(t, psideg)
plt.title('Flight Path Angle vs Time')
plt.xlabel('Time (s)')
plt.ylabel('Flight Path Angle (deg)')
plt.grid(True)

# Polar Trajectory Plot (Top Right)
ax_polar = plt.subplot(3, 2, 2, projection='polar')

# Plot trajectory with different colors for each stage
stage_times = [0, tburn1, tburn1 + tburn2, tburn1 + tburn2 + tcoast, tburn1 + tburn2 + tcoast + tburn3_1, tburn1 + tburn2 + tcoast + tburn3_1 + tcoast3, t_max]
stage_colors = ['blue', 'green', 'orange', 'purple', 'red', 'cyan']

for i in range(len(stage_times) - 1):
    mask = (t >= stage_times[i]) & (t < stage_times[i + 1])
    ax_polar.plot(theta[mask], htot[mask], label=f'Stage {i + 1}', color=stage_colors[i])

ax_polar.plot(Rearraytheta, Rearray, label='Earth', color='black')  # Earth circle
ax_polar.set_title('Polar Trajectory (Distance vs Angle)')
ax_polar.set_rticks([2000, 4000, 6000])  # Example ticks
ax_polar.set_rlabel_position(-22.5)  # Move radial labels away from plotted line
ax_polar.grid(True)
ax_polar.legend(loc='lower left')

# Downrange Distance vs Time (Middle Right)
plt.subplot(3, 2, 4)
plt.plot(t, dr)
plt.title('Downrange Distance vs Time')
plt.xlabel('Time (s)')
plt.ylabel('Downrange Distance (km)')
plt.grid(True)

# Height vs Downrange Distance (Bottom Right)
plt.subplot(3, 2, 6)
plt.plot(dr, h)
plt.title('Trajectory (Altitude vs Downrange Distance)')
plt.xlabel('Downrange Distance (km)')
plt.ylabel('Altitude (km)')
plt.grid(True)
plt.axis('equal')  # Optional: makes axes scale equally

plt.tight_layout()
plt.show()
