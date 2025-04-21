import { useState, lazy, Suspense } from "react"; // Import lazy and Suspense
import Earth from "./components/EarthScene";
// Dynamically import MoonScene
const MoonScene = lazy(() => import("./components/MoonScene"));

function App() {
  window.CESIUM_BASE_URL = "/cesium/"; // Example path, adjust as needed
  const [currentScene, setCurrentScene] = useState("earth"); // State to manage scene

  // Callback function to switch scenes
  const handleEarthSceneEnd = () => {
    console.log("Switching to Moon Scene");
    setCurrentScene("moon");
  };

  return (
    <div>
      {/* Conditionally render Earth scene */}
      {currentScene === "earth" && (
        <Earth onEarthSceneEnd={handleEarthSceneEnd} />
      )}
      {/* Conditionally render Moon scene with Suspense */}
      {currentScene === "moon" && (
        <Suspense fallback={<div>Loading Moon...</div>}>
          <MoonScene />
        </Suspense>
      )}
    </div>
  );
}

export default App;
