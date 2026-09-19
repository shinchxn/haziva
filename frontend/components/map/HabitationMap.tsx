"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import maplibregl from "maplibre-gl";

import "maplibre-gl/dist/maplibre-gl.css";

import type { HabitationSummary } from "@/types/api";

interface HabitationMapProps {
  habitations: HabitationSummary[];
  selectedId?: string | null;
  onSelect?: (id: string) => void;
}

export default function HabitationMap({
  habitations,
  selectedId,
  onSelect,
}: HabitationMapProps) {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const markers = useRef<maplibregl.Marker[]>([]);
  const router = useRouter();

  useEffect(() => {
    if (!mapContainer.current || map.current) {
      return;
    }

    const newMap = new maplibregl.Map({
      container: mapContainer.current,
      style: "https://demotiles.maplibre.org/style.json",
      center: [76.04, 11.61],
      zoom: 10,
    });

    newMap.addControl(
      new maplibregl.NavigationControl(),
      "top-right",
    );

    map.current = newMap;

    return () => {
      markers.current.forEach((marker) => marker.remove());
      markers.current = [];

      newMap.remove();
      map.current = null;
    };
  }, []);

  useEffect(() => {
    const currentMap = map.current;

    if (!currentMap || habitations.length === 0) {
      return;
    }

    const addMarkers = () => {
      markers.current.forEach((marker) => marker.remove());
      markers.current = [];

      habitations.forEach((habitation) => {
        const markerColor =
          habitation.current_risk >= 0.75
            ? "#dc2626"
            : habitation.current_risk >= 0.5
              ? "#f59e0b"
              : "#16a34a";

        const isSelected =
          selectedId === habitation.id;

        const markerElement =
          document.createElement("div");

        markerElement.style.position = "relative";
        markerElement.style.width = "18px";
        markerElement.style.height = "18px";
        markerElement.style.borderRadius = "50%";
        markerElement.style.backgroundColor =
          markerColor;
        markerElement.style.border = isSelected
          ? "3px solid #0f172a"
          : "3px solid white";
        markerElement.style.boxShadow =
          "0 2px 6px rgba(0,0,0,0.35)";
        markerElement.style.cursor = "pointer";
        markerElement.style.zIndex = "10";

        const label = document.createElement("div");

        label.textContent = habitation.name;

        label.style.position = "absolute";
        label.style.left = "14px";
        label.style.top = "50%";
        label.style.transform = "translateY(-50%)";

        label.style.backgroundColor = "white";
        label.style.border = "1px solid #cbd5e1";
        label.style.borderRadius = "6px";
        label.style.padding = "4px 8px";

        label.style.fontSize = "12px";
        label.style.fontWeight = "600";
        label.style.color = "#0f172a";

        label.style.whiteSpace = "nowrap";
        label.style.boxShadow =
          "0 1px 4px rgba(0,0,0,0.2)";

        label.style.pointerEvents = "none";
        label.style.zIndex = "20";

        markerElement.appendChild(label);

        const popup = new maplibregl.Popup({
          offset: 15,
          closeButton: true,
        }).setHTML(`
          <div style="min-width: 170px; padding: 2px;">
            <div style="font-size: 15px; font-weight: 600; color: #0f172a;">
              ${habitation.name}
            </div>

            <div style="margin-top: 8px; font-size: 13px; color: #475569;">
              Current Risk:
              <strong style="color: #0f172a;">
                ${(habitation.current_risk * 100).toFixed(0)}%
              </strong>
            </div>

            <div style="margin-top: 4px; font-size: 13px; color: #475569;">
              Priority:
              <strong style="color: #0f172a;">
                ${habitation.priority}
              </strong>
            </div>
          </div>
        `);

        const marker = new maplibregl.Marker({
          element: markerElement,
        })
          .setLngLat([
            habitation.longitude,
            habitation.latitude,
          ])
          .setPopup(popup)
          .addTo(currentMap);

        markerElement.addEventListener("click", () => {
          onSelect?.(habitation.id);

          currentMap.flyTo({
            center: [
              habitation.longitude,
              habitation.latitude,
            ],
            zoom: 12,
            duration: 800,
          });

          router.push(
            `/habitations?id=${habitation.id}`,
          );
        });

        markers.current.push(marker);
      });
    };

    if (currentMap.loaded()) {
      addMarkers();
    } else {
      currentMap.once("load", addMarkers);
    }

    return () => {
      markers.current.forEach((marker) => marker.remove());
      markers.current = [];
    };
  }, [habitations, selectedId, onSelect, router]);

  return (
    <div className="relative">
      <div
        ref={mapContainer}
        className="h-[500px] w-full overflow-hidden rounded-xl"
      />

      <div className="absolute bottom-4 left-4 z-10 rounded-lg border border-slate-200 bg-white/95 p-3 shadow-md backdrop-blur-sm">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-600">
          Risk Level
        </p>

        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-green-600" />
            <span className="text-xs text-slate-700">
              Lower risk &lt; 50%
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-amber-500" />
            <span className="text-xs text-slate-700">
              Elevated risk 50–74%
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-red-600" />
            <span className="text-xs text-slate-700">
              High risk ≥ 75%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}