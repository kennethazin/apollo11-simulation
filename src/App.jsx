import { useState, lazy, Suspense } from "react"; // Import lazy and Suspense
import HomeScreen from "./components/HomeScreen";
import Earth from "./components/EarthScene";
// Dynamically import MoonScene
const MoonScene = lazy(() => import("./components/MoonScene"));

function App() {
  window.CESIUM_BASE_URL = "/cesium/"; // Example path, adjust as needed
  const [currentScene, setCurrentScene] = useState("home"); // Start with home screen

  // Callback function to switch scenes
  const handleEarthSceneEnd = () => {
    console.log("Switching to Moon Scene");
    setCurrentScene("moon");
  };

  // Handle scene selection from home screen
  const handleSceneSelect = (scene) => {
    console.log(`Selected scene: ${scene}`);
    setCurrentScene(scene);
  };

  return (
    <div>
      {/* Render Home Screen */}
      {currentScene === "home" && (
        <HomeScreen onSceneSelect={handleSceneSelect} />
      )}

      {/* Render Earth scene */}
      {currentScene === "earth" && (
        <Earth onEarthSceneEnd={handleEarthSceneEnd} />
      )}

      {/* Render Moon scene with Suspense */}
      {currentScene === "moon" && (
        <Suspense fallback={<div>Loading Moon...</div>}>
          <MoonScene />
        </Suspense>
      )}
    </div>
  );
}

export default App;
