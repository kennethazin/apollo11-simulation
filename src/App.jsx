import MoonScene from "./components/MoonScene";

function App() {
  window.CESIUM_BASE_URL = "/cesium/"; // Example path, adjust as needed

  return (
    <div>
      <MoonScene />
    </div>
  );
}

export default App;
