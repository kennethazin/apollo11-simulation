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

      async function initialize() {
        const czmlFilePath = "/csm_lm_trajectory.czml";
        try {
          const czmlDataSource = new Cesium.CzmlDataSource();
          await czmlDataSource.load(czmlFilePath);
          viewer.dataSources.add(czmlDataSource);

          const rocket = czmlDataSource.entities.getById("AscentStage");

          if (rocket) {
            // Ensure the rocket path remains visible
            if (rocket.path) {
              rocket.path.show = new Cesium.ConstantProperty(true);
            }

            // Check if position exists before creating VelocityOrientationProperty
            if (rocket.position) {
              const velocityOrientation =
                new Cesium.VelocityOrientationProperty(rocket.position);

              // Apply a fixed rotation to align the rocket model correctly
              const rotationMatrix = Cesium.Matrix3.fromRotationY(
                Cesium.Math.toRadians(90.0)
              );
              const rotationQuaternion =
                Cesium.Quaternion.fromRotationMatrix(rotationMatrix);
              rocket.orientation = new Cesium.CallbackProperty(
                (time, result) => {
                  const baseOrientation = velocityOrientation.getValue(
                    time,
                    result || new Cesium.Quaternion()
                  );

                  if (!baseOrientation) {
                    // Return a default orientation if baseOrientation is undefined
                    return Cesium.Quaternion.IDENTITY;
                  }

                  return Cesium.Quaternion.multiply(
                    baseOrientation,
                    rotationQuaternion,
                    result || new Cesium.Quaternion()
                  );
                },
                false
              );
            } else {
              console.error("Rocket position is undefined in the CZML file.");
            }

            rocket.viewFrom = new Cesium.ConstantProperty(
              new Cesium.Cartesian3(-4000, 500, 250) // Adjusted to move closer to the model
            );

            // Set the initial view to focus on the lunar module (DescentStage)
            if (rocket && rocket.position) {
              const position = rocket.position.getValue(
                Cesium.JulianDate.now()
              );
              if (position) {
                viewer.camera.flyTo({
                  destination: Cesium.Cartesian3.multiplyByScalar(
                    position,
                    2, // Scale the position vector to move closer to the model
                    new Cesium.Cartesian3()
                  ),
                  orientation: {
                    heading: Cesium.Math.toRadians(0),
                    pitch: Cesium.Math.toRadians(-45),
                    roll: 0,
                  },
                  duration: 3, // Smooth transition duration
                });
              } else {
                console.error(
                  "Rocket position is undefined at the current time."
                );
              }
            }
          } else {
            console.error("Entity 'DescentStage' not found in the CZML file.");
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
