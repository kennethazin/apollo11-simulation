import { useEffect, useRef } from "react"; // Remove useState, add useRef
import * as Cesium from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";
import fireImage from "../assets/fire.png";
import { Howl, Howler } from "howler";
// Define props interface
interface EarthProps {
  onEarthSceneEnd: () => void;
}

const Earth: React.FC<EarthProps> = ({ onEarthSceneEnd }) => {
  // Refs for viewer, listeners, etc.
  const viewerRef = useRef<Cesium.Viewer | null>(null);
  const onTickListenerRemoverRef = useRef<
    Cesium.Event.RemoveCallback | undefined
  >(undefined);
  const sceneSwitchTriggeredRef = useRef(false);

  // Enhanced audio structure to support multiple sounds per stage
  const audioRefs = useRef<{
    stageAudios: Record<
      string,
      Array<{
        howl: Howl;
        startTime?: Cesium.JulianDate;
        played?: boolean;
      }>
    >;
    radioAudios?: Record<string, Howl[]>;
    thrusterLoop?: Howl;
    ambientAudios?: Record<string, Howl>;
    currentStage?: string;
    spriteAudios?: Record<
      string,
      {
        howl: Howl;
        sprites: Record<string, [number, number]>;
      }
    >;
  }>({
    stageAudios: {},
    radioAudios: {},
    ambientAudios: {},
  });

  useEffect(() => {
    // Define stage time intervals with support for multiple audio sources
    const stageIntervals = {
      prelaunch: {
        start: Cesium.JulianDate.fromIso8601("1969-07-16T13:27:45Z"),
        stop: Cesium.JulianDate.fromIso8601("1969-07-16T13:32:00Z"),
        audioSources: [
          { src: "/audio/a11_t-0000415.mp3", volume: 0.5, loop: false },
          {
            src: "/audio/a11_t-0000135.mp3",
            volume: 0.5,
            loop: false,
            startTime: Cesium.JulianDate.fromIso8601("1969-07-16T13:30:22Z"), // T-1min 35sec
          },
        ],
      },
      stage1: {
        start: Cesium.JulianDate.fromIso8601("1969-07-16T13:32:00Z"),
        stop: Cesium.JulianDate.fromIso8601("1969-07-16T13:32:50Z"),
        audioSources: [
          { src: "/audio/rocket-blastoff.mp3", volume: 0.3, loop: false },
        ],
        radioSources: [],
      },
      stage2: {
        start: Cesium.JulianDate.fromIso8601("1969-07-16T13:34:55Z"),
        stop: Cesium.JulianDate.fromIso8601("1969-07-16T13:44:44Z"),
        audioSources: [
          { src: "/audio/a11_0000255.mp3", volume: 0.5, loop: false },
        ],
        radioSources: [],
      },
      // ...rest of stages with similar structure
    };

    // Load sprite-based audio
    audioRefs.current.spriteAudios = {
      missionAudio: {
        howl: new Howl({
          src: ["/audio/mission_audio.mp3"],
          sprite: {
            countdown: [0, 20000],
            liftoff: [21000, 5000],
            staging: [26000, 10000],
            // Add more sprite definitions as needed
          },
        }),
        sprites: {
          countdown: [0, 20000],
          liftoff: [21000, 5000],
          staging: [26000, 10000],
        },
      },
    };

    // Initialize thruster loop with spatial properties
    audioRefs.current.thrusterLoop = new Howl({
      src: "/audio/thruster-loop.mp3",
      loop: true,
      volume: 0.4,
      spatial: true, // Add this to enable spatial audio
      panningModel: "HRTF", // Optional: use HRTF for better 3D sound
      refDistance: 1, // Distance at which the volume is normal
      rolloffFactor: 1, // How quickly the sound drops off with distance
      distanceModel: "linear", // Linear, inverse or exponential
    });

    // Initialize audio sources for each stage
    Object.entries(stageIntervals).forEach(([stageName, stageData]) => {
      // Initialize main audio for stage
      audioRefs.current.stageAudios[stageName] = stageData.audioSources.map(
        (audio) => ({
          howl: new Howl({
            src: [audio.src],
            loop: audio.loop ?? true,
            volume: audio.volume ?? 0.5,
          }),
          startTime: audio.startTime,
          played: false,
        })
      );

      // Initialize radio comms for stage if available
      if (stageData.radioSources) {
        audioRefs.current.radioAudios = audioRefs.current.radioAudios || {};
        audioRefs.current.radioAudios[stageName] = stageData.radioSources.map(
          (audio) =>
            new Howl({
              src: [audio.src],
              loop: audio.loop ?? false,
              volume: audio.volume ?? 0.3,
            })
        );
      }
    });

    // Don't auto-play prelaunch audios - we'll handle this with the time check
    audioRefs.current.currentStage = "prelaunch";

    // Demo of playing a sprite
    audioRefs.current.spriteAudios?.missionAudio?.howl.play("countdown");

    (async () => {
      // Dynamically create the Cesium container
      const cesiumContainer = document.createElement("div");
      cesiumContainer.id = "cesiumContainer";
      cesiumContainer.style.width = "100vw";
      cesiumContainer.style.height = "100vh";
      document.getElementById("root")?.appendChild(cesiumContainer);

      async function initializeViewer() {
        const terrainProvider =
          await Cesium.CesiumTerrainProvider.fromIonAssetId(1);
        const viewer = new Cesium.Viewer("cesiumContainer", {
          terrainProvider,
          shouldAnimate: true,
          // Disable editor tools like terrain chooser
          sceneModePicker: false,
          baseLayerPicker: false,
          geocoder: false,
          homeButton: false,
          navigationHelpButton: false,
          infoBox: true,
        });

        // Configure Earth's atmosphere
        viewer.scene.globe.showGroundAtmosphere = true; // Enable ground atmosphere
        viewer.scene.skyAtmosphere.hueShift = 0.0; // Default blue hue
        viewer.scene.skyAtmosphere.saturationShift = 0.1; // Slightly increase saturation
        viewer.scene.skyAtmosphere.brightnessShift = 0.1; // Make atmosphere slightly brighter

        // Make atmosphere more visible from space
        viewer.scene.skyAtmosphere.atmosphereRayleighCoefficient =
          new Cesium.Cartesian3(5.5e-6, 13.0e-6, 28.4e-6);
        viewer.scene.skyAtmosphere.atmosphereMieCoefficient =
          new Cesium.Cartesian3(21e-6, 21e-6, 21e-6);

        // Explicitly set the start time to match the mission timeline
        const startTime = Cesium.JulianDate.fromIso8601("1969-07-16T13:27:45Z");
        viewer.clock.currentTime = startTime;
        viewer.clock.startTime = startTime;
        viewer.clock.clockRange = Cesium.ClockRange.LOOP_STOP;

        return viewer;
      }

      const viewer = await initializeViewer();

      try {
        const tileset = await Cesium.Cesium3DTileset.fromIonAssetId(96188);
        viewer.scene.primitives.add(tileset);
        await viewer.zoomTo(tileset);

        // Apply the default style if it exists
        const extras = tileset.asset.extras;
        if (
          Cesium.defined(extras) &&
          Cesium.defined(extras.ion) &&
          Cesium.defined(extras.ion.defaultStyle)
        ) {
          tileset.style = new Cesium.Cesium3DTileStyle(extras.ion.defaultStyle);
        }
      } catch (error) {
        console.log(error);
      }

      viewer.scene.globe.depthTestAgainstTerrain = true;

      viewerRef.current = viewer; // Store viewer instance

      async function initialize() {
        const czmlFilePath = "/saturn_v_trajectory_with_delay.czml"; // Correct path to match the actual file
        try {
          console.log("Loading CZML file from:", czmlFilePath);
          const czmlDataSource = new Cesium.CzmlDataSource();
          await czmlDataSource.load(czmlFilePath);
          viewer.dataSources.add(czmlDataSource);

          // Debug all entities in the CZML
          console.log(
            "CZML loaded. Total entities:",
            czmlDataSource.entities.values.length
          );
          czmlDataSource.entities.values.forEach((entity) => {
            console.log(
              `Entity ID: ${entity.id}, Name: ${entity.name}, Has model: ${Boolean(entity.model)}`
            );
            if (entity.model && entity.model.uri) {
              console.log(
                `Model URI for ${entity.id}:`,
                entity.model.uri.getValue()
              );
            }
          });

          const satellite = czmlDataSource.entities.getById("SaturnV");
          const postTLI = czmlDataSource.entities.getById("Post-TLI");

          if (satellite && postTLI) {
            console.log("Found both Saturn V and Post-TLI entities");

            // Explicitly set Saturn V to be visible and ensure it has correct properties
            satellite.show = new Cesium.ConstantProperty(true);

            // Configure Saturn V model if needed
            if (satellite.model) {
              satellite.model.minimumPixelSize = new Cesium.ConstantProperty(
                128
              );
              satellite.model.maximumScale = new Cesium.ConstantProperty(20000);
              console.log("Saturn V model configured");
            } else {
              console.error("Saturn V entity doesn't have a model property!");
            }

            // Preload the LM model but keep it hidden initially
            postTLI.show = new Cesium.ConstantProperty(false);

            // Ensure the model path is correctly configured
            if (postTLI.model) {
              // Optional: Adjust model scale or appearance if needed
              postTLI.model.maximumScale = new Cesium.ConstantProperty(20000);
              postTLI.model.minimumPixelSize = new Cesium.ConstantProperty(64);

              // Debug the model URI to ensure it's correctly set
              console.log("Post-TLI model URI:", postTLI.model.uri?.getValue());
            }

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

            // Define the actual liftoff time for comparison
            const liftoffTime = Cesium.JulianDate.fromIso8601(
              "1969-07-16T13:32:00Z"
            );

            satellite.orientation = new Cesium.CallbackProperty(
              (time, result) => {
                // Check if we're in pre-launch phase
                if (time && Cesium.JulianDate.compare(time, liftoffTime) < 0) {
                  // Get the position at the current time
                  const position = satellite.position.getValue(
                    time,
                    new Cesium.Cartesian3()
                  );

                  if (position) {
                    // Calculate the transform at this position to get proper "up" direction
                    const transform =
                      Cesium.Transforms.eastNorthUpToFixedFrame(position);

                    // Extract just the rotation component to get a "pointing up" orientation
                    const rotation = Cesium.Matrix4.getMatrix3(
                      transform,
                      new Cesium.Matrix3()
                    );

                    // Add a fixed rotation if needed to align the model correctly
                    const fixedRotation = Cesium.Matrix3.fromRotationY(
                      Cesium.Math.toRadians(0.0)
                    );
                    Cesium.Matrix3.multiply(rotation, fixedRotation, rotation);

                    return Cesium.Quaternion.fromRotationMatrix(
                      rotation,
                      result || new Cesium.Quaternion()
                    );
                  }

                  // Fallback if position is undefined
                  return Cesium.Quaternion.IDENTITY.clone(result);
                }

                // After launch: use velocity-based orientation
                // Get base orientation
                const baseOrientation = velocityOrientation.getValue(
                  time,
                  result || new Cesium.Quaternion()
                );

                // Check if baseOrientation is defined before attempting to multiply
                if (Cesium.defined(baseOrientation)) {
                  return Cesium.Quaternion.multiply(
                    baseOrientation,
                    rotationQuaternion,
                    result || new Cesium.Quaternion()
                  );
                } else {
                  // Fallback orientation when velocity orientation is unavailable
                  return rotationQuaternion.clone(result);
                }
              },
              false
            );

            // Create orientation for CSM-LM
            const postTLIVelocityOrientation =
              new Cesium.VelocityOrientationProperty(postTLI.position);

            // Apply appropriate rotation for CSM-LM model
            postTLI.orientation = new Cesium.CallbackProperty(
              (time, result) => {
                const baseOrientation = postTLIVelocityOrientation.getValue(
                  time,
                  result || new Cesium.Quaternion()
                );
                // Add defensive check for baseOrientation
                if (Cesium.defined(baseOrientation)) {
                  // Adjust rotation if needed for CSM-LM model orientation
                  return baseOrientation;
                } else {
                  // Return identity quaternion as fallback
                  return Cesium.Quaternion.IDENTITY.clone(result);
                }
              },
              false
            );

            satellite.viewFrom = new Cesium.ConstantProperty(
              new Cesium.Cartesian3(-300, 20, 100)
            );

            // Set a similar viewFrom for Post-TLI
            postTLI.viewFrom = new Cesium.ConstantProperty(
              new Cesium.Cartesian3(-300, 20, 100)
            );

            // Set the camera to follow the satellite by default
            viewer.trackedEntity = satellite;

            // Set up a clock event listener
            const onTickListener = () => {
              if (!viewerRef.current || sceneSwitchTriggeredRef.current) return;

              const currentTime = viewerRef.current.clock.currentTime;

              // Ensure the TLI end time is correctly formatted
              const correctedTliEndTime = Cesium.JulianDate.fromIso8601(
                "1969-07-16T15:22:13Z"
              );

              // Debug current time and comparison
              if (
                Cesium.JulianDate.compare(currentTime, correctedTliEndTime) >= 0
              ) {
                console.log("Current time has reached or passed TLI end time");
              }

              // Logic for switching tracked entity (SaturnV -> Post-TLI)
              if (
                viewerRef.current.trackedEntity === satellite &&
                Cesium.JulianDate.compare(currentTime, correctedTliEndTime) >= 0
              ) {
                console.log(
                  "Switching tracked entity to Post-TLI at",
                  Cesium.JulianDate.toIso8601(currentTime)
                );

                // Hide SaturnV entity
                satellite.show = false;
                if (satellite.path) {
                  satellite.path.show = new Cesium.ConstantProperty(false);
                }

                // Show Post-TLI entity
                postTLI.show = true;
                if (postTLI.path) {
                  postTLI.path.show = new Cesium.ConstantProperty(true);
                }

                // Switch tracked entity
                viewerRef.current.trackedEntity = postTLI;

                // Zoom to the Post-TLI entity for better visibility
                viewerRef.current
                  .zoomTo(postTLI)
                  .then(() => {
                    console.log("Camera zoomed to Post-TLI entity");
                  })
                  .catch((error) => {
                    console.error("Failed to zoom to Post-TLI entity:", error);
                  });
              }

              // Define the time to trigger the scene switch
              const earthSceneEndTime = Cesium.JulianDate.fromIso8601(
                "1969-07-16T16:50:00Z" // Time when Earth scene should end
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

            // Add a clock event listener to check for audio playback based on time
            viewer.clock.onTick.addEventListener(() => {
              const currentJulianTime = viewer.clock.currentTime;

              // Find current stage
              let currentStage = null;
              for (const [stageName, interval] of Object.entries(
                stageIntervals
              )) {
                if (
                  Cesium.JulianDate.compare(
                    currentJulianTime,
                    interval.start
                  ) >= 0 &&
                  Cesium.JulianDate.compare(currentJulianTime, interval.stop) <=
                    0
                ) {
                  currentStage = stageName;
                  break;
                }
              }

              // Check all stage audio for time-based playback, regardless of current stage
              Object.entries(audioRefs.current.stageAudios).forEach(
                ([stageName, audioItems]) => {
                  audioItems.forEach((audioItem) => {
                    if (audioItem.played) return; // Skip if already played

                    const shouldPlay = audioItem.startTime
                      ? Cesium.JulianDate.compare(
                          currentJulianTime,
                          audioItem.startTime
                        ) >= 0
                      : stageName === currentStage; // Play if no startTime but we're in this stage

                    if (shouldPlay) {
                      audioItem.howl.play();
                      audioItem.played = true;
                    }
                  });
                }
              );

              // Handle stage transitions for non-audio elements (like sprites)
              if (
                currentStage &&
                currentStage !== audioRefs.current.currentStage
              ) {
                console.log(`Transitioning to ${currentStage} stage`);

                // Play any relevant sprite for this stage
                const relevantSprite = getSpriteForStage(currentStage);
                if (
                  relevantSprite &&
                  audioRefs.current.spriteAudios?.missionAudio
                ) {
                  audioRefs.current.spriteAudios.missionAudio.howl.play(
                    relevantSprite
                  );
                }

                // Play any radio communications for this stage
                playRandomRadioForStage(currentStage);

                audioRefs.current.currentStage = currentStage;
              }
            });
          } else {
            console.error(
              "Entity loading failed. SaturnV found:",
              Boolean(satellite),
              "Post-TLI found:",
              Boolean(postTLI)
            );
          }

          // Optimized particle system for thrusters
          const thrusterParticles = new Cesium.ParticleSystem({
            image: fireImage, // Path to particle image
            startColor: Cesium.Color.RED.withAlpha(0.7), // Reduce opacity for better blending
            endColor: Cesium.Color.ORANGE.withAlpha(0.5), // Reduce opacity for better blending
            startScale: 50.0, // Adjust scale for performance
            endScale: 1.0, // Gradually
            minimumParticleLife: 0.5, // Increase minimum particle life
            maximumParticleLife: 1.0, // Increase maximum particle life
            minimumSpeed: 5.0, // Increase minimum speed
            maximumSpeed: 10.0, // Increase maximum speed
            emissionRate: 50, // Increase emission rate for more particles
            emitter: new Cesium.ConeEmitter(Cesium.Math.toRadians(45)), // Widen the emission cone
            modelMatrix: Cesium.Matrix4.IDENTITY,
            lifetime: 160.0, // Increase lifetime for longer visibility
          });

          viewer.scene.primitives.add(thrusterParticles);

          function updateThrusterParticles() {
            const currentJulianTime = viewer.clock.currentTime;

            // Define burn times using JulianDate for accurate comparison
            // We'll reuse these for particle effects
            const burnIntervals = [
              new Cesium.TimeInterval({
                start: Cesium.JulianDate.fromIso8601("1969-07-16T13:32:00Z"), // Launch
                stop: Cesium.JulianDate.fromIso8601("1969-07-16T13:34:44Z"), // tburn1 = 164s
              }), // Stage 1
              new Cesium.TimeInterval({
                start: Cesium.JulianDate.fromIso8601("1969-07-16T13:34:45Z"), // After Stage 1
                stop: Cesium.JulianDate.fromIso8601("1969-07-16T13:41:15Z"), // tburn1 + tburn2 = 164s + 391s = 555s
              }), // Stage 2
              new Cesium.TimeInterval({
                start: Cesium.JulianDate.fromIso8601("1969-07-16T13:41:16Z"), // After Stage 2
                stop: Cesium.JulianDate.fromIso8601("1969-07-16T13:43:45Z"), // tburn1 + tburn2 + tburn3_1 = 164s + 391s + 150s = 705s
              }), // Stage 3 Burn 1
              new Cesium.TimeInterval({
                start: Cesium.JulianDate.fromIso8601("1969-07-16T16:16:16Z"), // After Coast, TLI start
                stop: Cesium.JulianDate.fromIso8601("1969-07-16T16:22:13Z"), // TLI end
              }), // Stage 3 Burn 2 (TLI)
            ];

            // Check if current time is within any burn interval (for particle effects)
            const isBurning = burnIntervals.some((interval) =>
              Cesium.TimeInterval.contains(interval, currentJulianTime)
            );

            // Determine which entity is currently active
            const activeEntity =
              viewer.trackedEntity === postTLI ? postTLI : satellite;

            thrusterParticles.show = isBurning && activeEntity === satellite; // Only show for SaturnV burns

            // Manage thruster audio independently
            if (isBurning && activeEntity === satellite) {
              // Thruster is active, play thruster sound if not already playing
              if (!audioRefs.current.thrusterLoop?.playing()) {
                audioRefs.current.thrusterLoop?.play();
              }

              // Calculate distance from camera to rocket for spatial audio
              if (audioRefs.current.thrusterLoop) {
                const cameraPosition = viewer.camera.positionWC; // Use world coordinates
                const rocketPosition = activeEntity?.position?.getValue(
                  currentJulianTime,
                  new Cesium.Cartesian3()
                );

                if (rocketPosition) {
                  // Set Howler's listener position to the camera's world position
                  Howler.pos(
                    cameraPosition.x,
                    cameraPosition.y,
                    cameraPosition.z
                  );

                  // Set the thruster sound's position to the rocket's world position
                  audioRefs.current.thrusterLoop.pos(
                    rocketPosition.x,
                    rocketPosition.y,
                    rocketPosition.z
                  );

                  // Remove manual volume adjustment; let Howler's spatial audio handle it
                }
              }
            } else {
              // No thrusters, stop thruster sound
              audioRefs.current.thrusterLoop?.stop();
            }

            // Determine current stage based on time
            let currentStage = null;
            for (const [stageName, interval] of Object.entries(
              stageIntervals
            )) {
              if (
                Cesium.JulianDate.compare(currentJulianTime, interval.start) >=
                  0 &&
                Cesium.JulianDate.compare(currentJulianTime, interval.stop) <= 0
              ) {
                currentStage = stageName;
                break;
              }
            }

            // Handle stage audio transitions and manage multiple audio sources
            if (
              currentStage &&
              currentStage !== audioRefs.current.currentStage
            ) {
              console.log(`Transitioning to ${currentStage} audio`);

              // Don't stop currently playing audio to allow overlapping

              // Only set the current stage - we'll handle audio playback in the tick listener
              audioRefs.current.currentStage = currentStage;
            }

            // Rest of thruster particle positioning logic
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
                const thrusterOffset = new Cesium.Cartesian3(0, 0, 0); // Example offset (adjust Z value)

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

          // Helper function to play random radio communication for current stage
          function playRandomRadioForStage(stage: string) {
            const radioAudios = audioRefs.current.radioAudios?.[stage];
            if (radioAudios && radioAudios.length > 0) {
              // Randomly select a radio clip to play
              const randomIndex = Math.floor(
                Math.random() * radioAudios.length
              );
              radioAudios[randomIndex]?.play();
            }
          }

          // Helper function to determine which sprite to play for a given stage
          function getSpriteForStage(stage: string): string | null {
            switch (stage) {
              case "prelaunch":
                return "countdown";
              case "stage1":
                return "liftoff";
              case "stage2":
                return "staging";
              // Map other stages to sprites as needed
              default:
                return null;
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
            lensFlare.uniforms.earthRadius =
              Cesium.Ellipsoid.WGS84.maximumRadius;

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
      await initialize();
    })();
    initialize();

    // Cleanup function
    return () => {
      console.log("Cleaning up EarthScene");

      // Stop all audio
      if (audioRefs.current) {
        // Stop all stage audio
        Object.values(audioRefs.current.stageAudios).forEach((audios) => {
          audios.forEach((audio) => audio.howl.stop());
        });

        // Stop all radio audio
        Object.values(audioRefs.current.radioAudios || {}).forEach((audios) => {
          audios.forEach((audio) => audio.stop());
        });

        // Stop thruster and sprite audio
        audioRefs.current.thrusterLoop?.stop();

        // Stop all sprites
        Object.values(audioRefs.current.spriteAudios || {}).forEach(
          (spriteAudio) => spriteAudio.howl.stop()
        );
      }

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
  }, [onEarthSceneEnd]);

  return null; // No need to return a JSX element
};

export default Earth;
function initialize() {
  throw new Error("Function not implemented.");
}
