"use client";

import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";

import "maplibre-gl/dist/maplibre-gl.css";

import { OPENFREEMAP_LIBERTY_STYLE } from "@/lib/mapStyle";
import type {
  HabitationDetail,
  RelocationSite,
} from "@/types/api";



interface RelocationMapProps {
  habitation: HabitationDetail;
  sites: RelocationSite[];
}

interface Coordinates {
  longitude: number;
  latitude: number;
}

function getSiteCoordinates(
  site: RelocationSite,
): Coordinates | null {
  const location = site.location;

  if (!location || typeof location !== "object") {
    return null;
  }

  const coordinates = (
    location as {
      coordinates?: unknown;
    }
  ).coordinates;

  if (!Array.isArray(coordinates)) {
    return null;
  }

  if (
    typeof coordinates[0] !== "number" ||
    typeof coordinates[1] !== "number"
  ) {
    return null;
  }

  return {
    longitude: coordinates[0],
    latitude: coordinates[1],
  };
}

function createMarkerElement(
  color: string,
  label: string,
) {
  const wrapper = document.createElement("div");

  wrapper.style.position = "relative";
  wrapper.style.width = "22px";
  wrapper.style.height = "22px";
  wrapper.style.cursor = "pointer";

  const dot = document.createElement("div");

  dot.style.width = "22px";
  dot.style.height = "22px";
  dot.style.borderRadius = "50%";
  dot.style.backgroundColor = color;
  dot.style.border = "4px solid white";
  dot.style.boxShadow =
    "0 2px 8px rgba(0,0,0,0.35)";

  const labelElement = document.createElement("div");

  labelElement.textContent = label;

  labelElement.style.position = "absolute";
  labelElement.style.left = "30px";
  labelElement.style.top = "-4px";
  labelElement.style.whiteSpace = "nowrap";
  labelElement.style.backgroundColor = "white";
  labelElement.style.border = "1px solid #e2e8f0";
  labelElement.style.borderRadius = "6px";
  labelElement.style.padding = "4px 8px";
  labelElement.style.fontSize = "12px";
  labelElement.style.fontWeight = "600";
  labelElement.style.color = "#0f172a";
  labelElement.style.boxShadow =
    "0 2px 6px rgba(0,0,0,0.15)";
  labelElement.style.pointerEvents = "none";

  wrapper.appendChild(dot);
  wrapper.appendChild(labelElement);

  return wrapper;
}

export default function RelocationMap({
  habitation,
  sites,
}: RelocationMapProps) {
  const mapContainer = useRef<HTMLDivElement | null>(
    null,
  );

  const map = useRef<maplibregl.Map | null>(null);

  const markers = useRef<maplibregl.Marker[]>([]);

  useEffect(() => {
    if (!mapContainer.current || map.current) {
      return;
    }

    const newMap = new maplibregl.Map({
      container: mapContainer.current,
      style: OPENFREEMAP_LIBERTY_STYLE,
      center: [
        habitation.longitude,
        habitation.latitude,
      ],
      zoom: 11,
    });

    newMap.on("error", (e) => {
      console.warn("MapLibre event diagnostic:", e);
    });

    newMap.addControl(
      new maplibregl.NavigationControl(),
      "top-right",
    );



    map.current = newMap;

    return () => {
      markers.current.forEach((marker) =>
        marker.remove(),
      );

      markers.current = [];

      newMap.remove();
      map.current = null;
    };
  }, [
    habitation.latitude,
    habitation.longitude,
  ]);

  useEffect(() => {
    const currentMap = map.current;

    if (!currentMap) {
      return;
    }

    const addMarkers = () => {
      markers.current.forEach((marker) =>
        marker.remove(),
      );

      markers.current = [];

      /*
       * Selected habitation marker
       */
      const habitationElement =
        createMarkerElement(
          "#111827",
          habitation.name,
        );

      const habitationPopup =
        new maplibregl.Popup({
          offset: 15,
        }).setHTML(`
          <div style="min-width: 180px;">
            <div style="font-weight: 700; color: #111827;">
              ${habitation.name}
            </div>

            <div style="margin-top: 5px; color: #64748b;">
              Selected habitation
            </div>
          </div>
        `);

      const habitationMarker =
        new maplibregl.Marker({
          element: habitationElement,
        })
          .setLngLat([
            habitation.longitude,
            habitation.latitude,
          ])
          .setPopup(habitationPopup)
          .addTo(currentMap);

      markers.current.push(habitationMarker);

      /*
       * Relocation site markers
       */
      sites.forEach((site) => {
        const coordinates = getSiteCoordinates(site);

        if (!coordinates) {
          return;
        }

        const isCandidate =
          site.status.toLowerCase() === "candidate";

        const markerColor = isCandidate
          ? "#16a34a"
          : "#dc2626";

        const markerElement =
          createMarkerElement(
            markerColor,
            site.site_id,
          );

        const popup =
          new maplibregl.Popup({
            offset: 15,
          }).setHTML(`
            <div style="min-width: 190px;">
              <div style="font-weight: 700; color: #111827;">
                ${site.site_id}
              </div>

              <div style="margin-top: 6px; color: #475569;">
                Status:
                <strong>
                  ${site.status}
                </strong>
              </div>

              <div style="margin-top: 4px; color: #475569;">
                Safety:
                <strong>
                  ${site.safety}
                </strong>
              </div>

              <div style="margin-top: 4px; color: #475569;">
                Capacity:
                <strong>
                  ${site.capacity}
                </strong>
              </div>

              ${
                site.rejection_reason
                  ? `
                    <div style="margin-top: 8px; color: #b91c1c;">
                      ${site.rejection_reason}
                    </div>
                  `
                  : ""
              }
            </div>
          `);

        const marker = new maplibregl.Marker({
          element: markerElement,
        })
          .setLngLat([
            coordinates.longitude,
            coordinates.latitude,
          ])
          .setPopup(popup)
          .addTo(currentMap);

        markers.current.push(marker);
      });

      /*
       * Fit the map around the habitation and
       * all relocation sites.
       */
      const bounds = new maplibregl.LngLatBounds();

      bounds.extend([
        habitation.longitude,
        habitation.latitude,
      ]);

      sites.forEach((site) => {
        const coordinates = getSiteCoordinates(site);

        if (coordinates) {
          bounds.extend([
            coordinates.longitude,
            coordinates.latitude,
          ]);
        }
      });

      if (!bounds.isEmpty()) {
        currentMap.fitBounds(bounds, {
          padding: 90,
          maxZoom: 13,
          duration: 700,
        });
      }
    };

    if (currentMap.loaded()) {
      addMarkers();
    } else {
      currentMap.once("load", addMarkers);
    }

    return () => {
      markers.current.forEach((marker) =>
        marker.remove(),
      );

      markers.current = [];
    };
  }, [habitation, sites]);

  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-200">
      <div
        ref={mapContainer}
        className="h-[450px] w-full"
      />

      <div className="absolute bottom-4 left-4 rounded-lg border border-slate-200 bg-white p-3 shadow-md">
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-slate-900" />
            <span className="text-slate-700">
              Habitation
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-green-600" />
            <span className="text-slate-700">
              Candidate
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-red-600" />
            <span className="text-slate-700">
              Rejected
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}