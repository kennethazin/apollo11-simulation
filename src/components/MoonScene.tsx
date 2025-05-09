import React, { useEffect, useRef } from "react";
import * as Cesium from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";

// Set the default ellipsoid to Moon
Cesium.Ellipsoid.default = Cesium.Ellipsoid.MOON;

// Define Points of Interest and Camera Views outside the component
const pointsOfInterest = [
  { text: "Apollo 11", latitude: 0.67416, longitude: 23.47315 },
  { text: "Apollo 14", latitude: -3.64417, longitude: 342.52135 },
  { text: "Apollo 15", latitude: 26.13341, longitude: 3.6285 },
];

// Define key mission events
const missionEvents = [
  {
    label: "LM Undocking (17:44 UT)",
    time: "1969-07-20T17:44:00Z",
    description: "Eagle separates from Columbia",
  },
  {
    label: "Descent Orbit Insertion (19:08 UT)",
    time: "1969-07-20T19:08:00Z",
    description: "30-second burn to begin descent trajectory",
  },
  {
    label: "Powered Descent Initiation (20:05 UT)",
    time: "1969-07-20T20:05:00Z",
    description: "Final braking phase begins",
  },
  {
    label: "Lunar Touchdown (20:17:40 UT)",
    time: "1969-07-20T20:17:40Z",
    description: "Eagle lands at Tranquility Base",
  },
];

const MoonScene: React.FC = () => {
  const cesiumContainerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<Cesium.Viewer | null>(null);

  useEffect(() => {
    if (cesiumContainerRef.current && !viewerRef.current) {
      const viewer = new Cesium.Viewer(cesiumContainerRef.current, {
        baseLayer: false, // No base imagery layer
        timeline: true,
        animation: true,
        baseLayerPicker: false,
        geocoder: false,
        shadows: true,
      });
      viewerRef.current = viewer;
      const scene = viewer.scene;

      const startTime = Cesium.JulianDate.fromIso8601("1969-07-20T19:08:00Z");
      viewer.clock.currentTime = startTime;
      viewer.clock.startTime = startTime;
      viewer.clock.clockRange = Cesium.ClockRange.LOOP_STOP;

      scene.skyBox = Cesium.SkyBox.createEarthSkyBox();

      // Add Moon Terrain 3D Tiles
      Cesium.Cesium3DTileset.fromIonAssetId(2684829, {
        enableCollision: true,
      })
        .then((tileset) => {
          scene.primitives.add(tileset);
        })
        .catch((error) => {
          console.log(`Error loading tileset: ${error}`);
        });

      // Add Points of Interest
      pointsOfInterest.forEach((poi) => {
        viewer.entities.add({
          position: Cesium.Cartesian3.fromDegrees(poi.longitude, poi.latitude),
          label: {
            text: poi.text,
            font: "14pt Verdana",
            outlineColor: Cesium.Color.DARKSLATEGREY,
            outlineWidth: 2,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            pixelOffset: new Cesium.Cartesian2(0, -22),
            scaleByDistance: new Cesium.NearFarScalar(1.5e2, 1.0, 1.5e7, 0.5),
            translucencyByDistance: new Cesium.NearFarScalar(
              2.5e7,
              1.0,
              4.0e7,
              0.0
            ),
            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          },
          point: {
            pixelSize: 10,
            color: Cesium.Color.fromBytes(243, 242, 99),
            outlineColor: Cesium.Color.fromBytes(219, 218, 111),
            outlineWidth: 2,
            scaleByDistance: new Cesium.NearFarScalar(1.5e3, 1.0, 4.0e7, 0.1),
            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
          },
        });
      });

      // Add mission timeline events (log events for now)
      missionEvents.forEach((event) => {
        console.log(
          `Mission Event: ${event.label} - ${event.description} at ${event.time}`
        );
      });

      async function initialize() {
        const czmlFilePath = "/apollo11_mission.czml";
        try {
          // Set up clock settings before loading CZML
          const startTime = Cesium.JulianDate.fromIso8601(
            "1969-07-20T19:08:00Z"
          );
          const stopTime = Cesium.JulianDate.fromIso8601(
            "1969-07-21T21:00:00Z"
          );

          // Create data source with custom clock settings
          const czmlDataSource = new Cesium.CzmlDataSource({
            // Override the default CZML clock settings
            clock: new Cesium.DataSourceClock({
              startTime: startTime,
              currentTime: startTime,
              stopTime: stopTime,
              clockRange: Cesium.ClockRange.LOOP_STOP,
              multiplier: 1,
            }),
          });

          // Load CZML data
          await czmlDataSource.load(czmlFilePath);
          await viewer.dataSources.add(czmlDataSource);

          // Force viewer clock settings after CZML is loaded
          viewer.clock.startTime = startTime;
          viewer.clock.currentTime = startTime;
          viewer.clock.clockRange = Cesium.ClockRange.LOOP_STOP;
          viewer.clock.multiplier = 1;
          viewer.clock.shouldAnimate = true;

          // Setup proper orientation for both stages
          const descentStage = czmlDataSource.entities.getById("LM_Descent");
          const ascentStage = czmlDataSource.entities.getById("LM_Ascent");

          if (descentStage && descentStage.position) {
            descentStage.orientation = new Cesium.VelocityOrientationProperty(
              descentStage.position
            );
            descentStage.viewFrom = new Cesium.ConstantProperty(
              new Cesium.Cartesian3(0, 5000, 3000) // Further view for descent stage
            );

            viewer.trackedEntity = descentStage;
          }

          if (ascentStage && ascentStage.position) {
            ascentStage.orientation = new Cesium.VelocityOrientationProperty(
              ascentStage.position
            );
            ascentStage.viewFrom = new Cesium.ConstantProperty(
              new Cesium.Cartesian3(-100, 20, 50)
            );
          } else {
            console.error(
              "Descent stage position is undefined at the current time."
            );
          }
        } catch (error) {
          console.error(
            `Failed to load the CZML file from '${czmlFilePath}'.`,
            error
          );
        }
      }

      initialize();

      // Cleanup function
      return () => {
        if (viewerRef.current && !viewerRef.current.isDestroyed()) {
          viewerRef.current.destroy();
        }
        viewerRef.current = null;
      };
    }
  }, []);

  return (
    <div style={{ position: "relative", width: "100%", height: "100vh" }}>
      <div ref={cesiumContainerRef} style={{ width: "100%", height: "100%" }} />
    </div>
  );
};

export default MoonScene;
