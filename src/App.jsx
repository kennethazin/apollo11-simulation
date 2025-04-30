import { useState, lazy, Suspense, useEffect } from "react"; // Add useEffect import
import HomeScreen from "./components/HomeScreen";
import Earth from "./components/EarthScene";
import LoadingScreen from "./components/LoadingScreen";
// Dynamically import MoonScene
const MoonScene = lazy(() => import("./components/MoonScene"));

function App() {
  window.CESIUM_BASE_URL = "/cesium/"; // Example path, adjust as needed
  const [currentScene, setCurrentScene] = useState("home"); // Start with home screen
  const [isLoading, setIsLoading] = useState(false); // Add loading state
  const [nextScene, setNextScene] = useState(null); // Track the next scene to load

  // Callback function to switch scenes
  const handleEarthSceneEnd = () => {
    console.log("Switching to Moon Scene");
    setIsLoading(true);
    setNextScene("moon");
  };

  // Handle scene selection from home screen
  const handleSceneSelect = (scene) => {
    console.log(`Selected scene: ${scene}`);
    setIsLoading(true); // Start loading
    setNextScene(scene); // Set the next scene to load
  };

  // Effect to transition from loading to the actual scene
  useEffect(() => {
    if (isLoading && nextScene) {
      const timer = setTimeout(() => {
        setCurrentScene(nextScene);
        setIsLoading(false);
        setNextScene(null);
      }, 1); // Show loading screen for 3 seconds, adjust as needed

      return () => clearTimeout(timer);
    }
  }, [isLoading, nextScene]);

  return (
    <div>
      {/* Render Home Screen */}
      {currentScene === "home" && !isLoading && (
        <HomeScreen onSceneSelect={handleSceneSelect} />
      )}

      {/* Render Loading Screen */}
      {isLoading && (
        <LoadingScreen
          message={
            nextScene === "earth"
              ? "Preparing Earth launch sequence..."
              : "Initiating lunar landing module..."
          }
        />
      )}

      {/* Render Earth scene */}
      {currentScene === "earth" && !isLoading && (
        <Suspense
          fallback={
            <LoadingScreen message="Preparing Earth launch sequence..." />
          }
        >
          <Earth onEarthSceneEnd={handleEarthSceneEnd} />
        </Suspense>
      )}

      {/* Render Moon scene with Suspense */}
      {currentScene === "moon" && !isLoading && (
        <Suspense
          fallback={
            <LoadingScreen message="Initiating lunar landing module..." />
          }
        >
          <MoonScene />
        </Suspense>
      )}
    </div>
  );
}

export default App;
