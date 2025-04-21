import { useEffect, useRef } from "react"; // Remove useState, add useRef
import * as Cesium from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";

// Define props interface
interface EarthProps {
  onEarthSceneEnd: () => void;
}

const Earth: React.FC<EarthProps> = ({ onEarthSceneEnd }) => {
  // Destructure props
  // Remove earthSceneOver state: const [earthSceneOver, setEarthSceneOver] = useState(false);
  const viewerRef = useRef<Cesium.Viewer | null>(null); // Ref to store viewer instance
  const onTickListenerRemoverRef = useRef<
    Cesium.Event.RemoveCallback | undefined
  >(undefined); // Ref for listener remover
  const sceneSwitchTriggeredRef = useRef(false); // Ref to track if switch has been triggered

  useEffect(() => {
    // Dynamically create the Cesium container
    const cesiumContainer = document.createElement("div");
    cesiumContainer.id = "cesiumContainer";
    cesiumContainer.style.width = "100vw";
    cesiumContainer.style.height = "100vh";
    document.getElementById("root")?.appendChild(cesiumContainer);

    const viewer = new Cesium.Viewer(cesiumContainer, {
      terrain: Cesium.Terrain.fromWorldTerrain(),
      shouldAnimate: true, // Ensure animation is enabled for clock ticks
    });
    viewerRef.current = viewer; // Store viewer instance

    async function initialize() {
      const czmlFilePath = "/saturn_v_trajectory_orientation.czml";
      try {
        const czmlDataSource = new Cesium.CzmlDataSource();
        await czmlDataSource.load(czmlFilePath);
        viewer.dataSources.add(czmlDataSource);

        const satellite = czmlDataSource.entities.getById("SaturnV");
        const postTLI = czmlDataSource.entities.getById("Post-TLI");

        if (satellite && postTLI) {
          // Preload the LM model and path
          postTLI.show = false; // Initially hide the LM model

          // Ensure the Saturn V path remains visible after transition
          if (satellite.path) {
            satellite.path.show = new Cesium.ConstantProperty(true);
          }

          // Use VelocityOrientationProperty for automatic orientation
          const velocityOrientation = new Cesium.VelocityOrientationProperty(
            satellite.position
          );

          // Apply a fixed rotation to align the rocket model correctly
          const rotationMatrix = Cesium.Matrix3.fromRotationY(
            Cesium.Math.toRadians(90.0)
          );
          const rotationQuaternion =
            Cesium.Quaternion.fromRotationMatrix(rotationMatrix);
          satellite.orientation = new Cesium.CallbackProperty(
            (time, result) => {
              const baseOrientation = velocityOrientation.getValue(
                time,
                result || new Cesium.Quaternion()
              );
              return Cesium.Quaternion.multiply(
                baseOrientation,
                rotationQuaternion,
                result || new Cesium.Quaternion()
              );
            },
            false
          );

          satellite.viewFrom = new Cesium.ConstantProperty(
            new Cesium.Cartesian3(-300, 20, 100)
          );
          // Set the camera to follow the satellite by default
          viewer.trackedEntity = satellite;
          // Set up a clock event listener
          const onTickListener = () => {
            if (!viewerRef.current || sceneSwitchTriggeredRef.current) return; // Exit if viewer destroyed or switch already triggered

            const currentTime = viewerRef.current.clock.currentTime;
            const correctedTliEndTime = Cesium.JulianDate.fromIso8601(
              "1969-07-16T17:05:54Z"
            );

            // Logic for switching tracked entity (SaturnV -> Post-TLI)
            if (
              viewerRef.current.trackedEntity === satellite &&
              Cesium.JulianDate.compare(currentTime, correctedTliEndTime) >= 0
            ) {
              // ... (existing logic for switching to Post-TLI) ...
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
              // Stop the clock or remove the listener if desired after switching
              // viewerRef.current.clock.shouldAnimate = false;
              if (onTickListenerRemoverRef.current) {
                onTickListenerRemoverRef.current(); // Remove this specific listener
                onTickListenerRemoverRef.current = undefined;
              }
            }
          };
          // Add the listener and store the remover function
          onTickListenerRemoverRef.current =
            viewer.clock.onTick.addEventListener(onTickListener);
        } else {
          console.error(
            "Entities 'SaturnV' or 'Post-TLI' not found in the CZML file."
          );
        }

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

        viewer.scene.primitives.add(thrusterParticles);

        function updateThrusterParticles() {
          const currentJulianTime = viewer.clock.currentTime; // Use JulianDate for comparison
          const currentTimeMs =
            Cesium.JulianDate.toDate(currentJulianTime).getTime();

          // Define burn times using JulianDate for accurate comparison
          const burnIntervals = [
            new Cesium.TimeInterval({
              start: Cesium.JulianDate.fromIso8601("1969-07-16T13:32:00Z"),
              stop: Cesium.JulianDate.fromIso8601("1969-07-16T13:34:48Z"),
            }), // Stage 1
            new Cesium.TimeInterval({
              start: Cesium.JulianDate.fromIso8601("1969-07-16T13:34:48Z"),
              stop: Cesium.JulianDate.fromIso8601("1969-07-16T13:40:54Z"),
            }), // Stage 2
            new Cesium.TimeInterval({
              start: Cesium.JulianDate.fromIso8601("1969-07-16T13:40:54Z"),
              stop: Cesium.JulianDate.fromIso8601("1969-07-16T13:43:18Z"),
            }), // Stage 3 Burn 1
            new Cesium.TimeInterval({
              start: Cesium.JulianDate.fromIso8601("1969-07-16T16:59:18Z"),
              stop: Cesium.JulianDate.fromIso8601("1969-07-16T17:05:54Z"), // Corrected TLI end time
            }), // Stage 3 Burn 2 (TLI)
          ];

          // Check if current time is within any burn interval
          const isBurning = burnIntervals.some((interval) =>
            Cesium.TimeInterval.contains(interval, currentJulianTime)
          );

          // Determine which entity is currently active
          const activeEntity =
            viewer.trackedEntity === postTLI ? postTLI : satellite;

          thrusterParticles.show = isBurning && activeEntity === satellite; // Only show for SaturnV burns

          if (activeEntity && isBurning && activeEntity === satellite) {
            // Ensure position and orientation exist before accessing them
            const position = activeEntity.position?.getValue(
              currentJulianTime,
              new Cesium.Cartesian3()
            );
            const orientation = activeEntity.orientation?.getValue(
              currentJulianTime,
              new Cesium.Quaternion()
            );

            if (position && orientation) {
              // Calculate the offset for the thruster position relative to the model's center
              // This offset needs to be in the model's local coordinate system.
              // Assuming the thruster is at the 'bottom' (e.g., -Z direction) of the rocket model.
              // Adjust the offset vector (e.g., new Cesium.Cartesian3(0, 0, -15)) based on your model's size and orientation.
              const thrusterOffset = new Cesium.Cartesian3(0, 0, -25); // Example offset (adjust Z value)

              // Get the model matrix (position and orientation)
              const modelMatrix =
                Cesium.Transforms.headingPitchRollToFixedFrame(
                  position,
                  Cesium.HeadingPitchRoll.fromQuaternion(orientation)
                );

              // Transform the offset from the model's local frame to world coordinates
              const thrusterPosition = Cesium.Matrix4.multiplyByPoint(
                modelMatrix,
                thrusterOffset,
                new Cesium.Cartesian3()
              );

              // Create a translation matrix for the thruster position
              const translationMatrix = Cesium.Matrix4.fromTranslation(
                thrusterPosition,
                new Cesium.Matrix4()
              );

              // Get the rotation matrix from the orientation quaternion
              const rotationMatrix = Cesium.Matrix3.fromQuaternion(
                orientation,
                new Cesium.Matrix3()
              );

              // Combine translation and rotation for the particle emitter's model matrix
              // We want the particles to emit *from* the thruster position, oriented with the rocket.
              const emitterModelMatrix = Cesium.Matrix4.multiply(
                translationMatrix,
                Cesium.Matrix4.fromRotationTranslation(
                  rotationMatrix,
                  Cesium.Cartesian3.ZERO
                ), // Use only rotation part
                new Cesium.Matrix4()
              );

              thrusterParticles.modelMatrix = emitterModelMatrix;

              // Update emitter direction if needed (e.g., ConeEmitter direction)
              // By default, ConeEmitter emits along the Z-axis. If your model's thruster
              // points differently relative to its orientation, you might need adjustments.
              // For a typical rocket, emitting 'down' (-Z) relative to orientation might be desired.
              // The VelocityOrientationProperty + rotation should handle the main orientation.
            }
          }
        }

        viewer.clock.onTick.addEventListener(updateThrusterParticles);

        const viewModel = {
          show: true,
          intensity: 2.0,
          distortion: 10.0,
          dispersion: 0.4,
          haloWidth: 0.4,
          dirtAmount: 0.4,
        };

        const lensFlare = viewer.scene.postProcessStages.add(
          Cesium.PostProcessStageLibrary.createLensFlareStage()
        );

        function updatePostProcess() {
          lensFlare.enabled = Boolean(viewModel.show);
          lensFlare.uniforms.intensity = Number(viewModel.intensity);
          lensFlare.uniforms.distortion = Number(viewModel.distortion);
          lensFlare.uniforms.ghostDispersal = Number(viewModel.dispersion);
          lensFlare.uniforms.haloWidth = Number(viewModel.haloWidth);
          lensFlare.uniforms.dirtAmount = Number(viewModel.dirtAmount);
          lensFlare.uniforms.earthRadius = Cesium.Ellipsoid.WGS84.maximumRadius;

          // Increase the resolution of the lens flare reflection
          lensFlare.uniforms.resolution = 1024; // Set a higher resolution value
        }
        updatePostProcess();

        // Add event listeners for buttons
        // document
        //   .getElementById("satelliteButton")
        //   .addEventListener("click", () => {
        //     viewer.clock.stopTime = satelliteStopTime;
        //     viewer.clock.currentTime = startTime;
        //     viewer.clock.multiplier = 30;
        //     viewer.timeline.zoomTo(startTime, satelliteStopTime);
        //     viewer.trackedEntity = satellite; // Ensure the camera follows the satellite
        //   });

        // document
        //   .getElementById("trackingAuto")
        //   .addEventListener("click", () => {
        //     satellite.trackingReferenceFrame =
        //       Cesium.TrackingReferenceFrame.AUTODETECT;
        //   });

        // document
        //   .getElementById("trackingInertial")
        //   .addEventListener("click", () => {
        //     satellite.trackingReferenceFrame =
        //       Cesium.TrackingReferenceFrame.INERTIAL;
        //   });

        // document
        //   .getElementById("trackingVelocity")
        //   .addEventListener("click", () => {
        //     satellite.trackingReferenceFrame =
        //       Cesium.TrackingReferenceFrame.VELOCITY;
        //   });

        // document.getElementById("trackingENU").addEventListener("click", () => {
        //   satellite.trackingReferenceFrame = Cesium.TrackingReferenceFrame.ENU;
        // });
      } catch (error) {
        if (error instanceof SyntaxError) {
          console.error(
            `Failed to parse the CZML file at '${czmlFilePath}'. Ensure the file contains valid CZML data.`,
            error
          );
        } else {
          console.error(
            `Failed to load the CZML file from '${czmlFilePath}'. Please check the file path and ensure the file is accessible.`,
            error
          );
        }
      }
    }

    initialize();

    // Cleanup function
    return () => {
      console.log("Cleaning up EarthScene");
      // Remove the specific onTick listener if it's still active
      if (onTickListenerRemoverRef.current) {
        console.log("Removing onTick listener");
        onTickListenerRemoverRef.current();
        onTickListenerRemoverRef.current = undefined;
      }
      // Remove other listeners if added separately (e.g., updateThrusterParticles)

      // Destroy the viewer instance
      if (viewerRef.current && !viewerRef.current.isDestroyed()) {
        console.log("Destroying Cesium viewer");
        viewerRef.current.destroy();
      }
      viewerRef.current = null;

      // Remove the dynamically created container
      const container = document.getElementById("cesiumContainer");
      if (container) {
        console.log("Removing Cesium container element");
        container.remove();
      }
      // Reset the trigger flag (optional, depends on component lifecycle)
      sceneSwitchTriggeredRef.current = false;
    };
  }, [onEarthSceneEnd]); // Add onEarthSceneEnd to dependency array

  return null; // No need to return a JSX element
};

export default Earth;
