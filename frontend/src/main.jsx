import React from "react";
import ReactDOM from "react-dom/client";

// Bootstrap primero, luego nuestro tema para sobrescribir la estética.
import "bootstrap/dist/css/bootstrap.min.css";
import "./styles/theme.css";

import App from "./App.jsx";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
