import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./index.css"; // Assuming you have some base CSS
import * as Cesium from "cesium";

Cesium.Ion.defaultAccessToken =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIxNDQyNGVkOS0wYTZiLTRjYzMtYTQ1OS02MzE3MGMzMTA3M2IiLCJpZCI6Mjk0NzEzLCJpYXQiOjE3NDQ4MTk0MjN9.7JtW3eBDF6Y7JUFOEYXvd4KjJQVSQ2kbo6NtfhchftQ";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
