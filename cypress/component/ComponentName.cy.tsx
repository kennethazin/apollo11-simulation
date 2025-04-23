import React from "react";
import Earth from "../../src/components/EarthScene";

describe("EarthScene.cy.tsx", () => {
  it("renders the Earth component", () => {
    const onEarthSceneEnd = cy.stub().as("onEarthSceneEnd");
    cy.mount(<Earth onEarthSceneEnd={onEarthSceneEnd} />);
    cy.get("#cesiumContainer").should("exist"); // Verify Cesium container is created
  });
});
