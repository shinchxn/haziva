"use client";

import { useEffect, useRef } from "react";
import { Map, NavigationControl, Marker, Popup } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

export default function MapView() {
  const mapContainer = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!mapContainer.current) return;

    const map = new Map({
      container: mapContainer.current,
      style: {
  version: 8,
  sources: {
    osm: {
      type: "raster",
      tiles: [
        "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
      ],
      tileSize: 256,
      attribution: "© OpenStreetMap contributors"
    }
  },
  layers: [
    {
      id: "osm",
      type: "raster",
      source: "osm"
    }
  ]
},
      center: [76.1, 11.6],
      zoom: 9,
    });
    map.addControl(new NavigationControl(), "top-right");
    fetch("http://localhost:8000/habitations")
  .then((response) => response.json())
  .then((habititations) => {
    habititations.forEach((habitation: any) => {
      const marker = new Marker({
        color: habitation.current_risk >= 0.7
          ? "red"
          : habitation.current_risk >= 0.4
          ? "orange"
          : "green",
      })
        .setLngLat([
          habitation.longitude,
          habitation.latitude,
        ])
        .setPopup(
          new Popup().setHTML(`
            <h3>${habitation.name}</h3>
            <p>Risk: ${habitation.current_risk}</p>
            <p>Priority: ${habitation.priority}</p>
          `)
        )
        .addTo(map);
    });
  })
  .catch((error) => {
    console.error("Error loading habitations:", error);
  });

    return () => {
      map.remove();
    };
  }, []);

  return (
    <div
      ref={mapContainer}
      style={{
        width: "100%",
        height: "500px",
      }}
    />
  );
}
