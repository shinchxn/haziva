"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import maplibregl from "maplibre-gl";

import "maplibre-gl/dist/maplibre-gl.css";

import type { HabitationSummary } from "@/types/api";
import { RISK_COLORS, classifyRisk } from "@/lib/riskClassification";

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
  const rawGeoJson = useRef<GeoJSON.FeatureCollection | null>(null);
  const router = useRouter();

  // Helper to join habitation API risk data into GeoJSON polygon properties
  const enrichGeoJson = (
    geoJson: GeoJSON.FeatureCollection,
    habList: HabitationSummary[],
  ): GeoJSON.FeatureCollection => {
    const habByCode = new Map<string, HabitationSummary>();
    const habByName = new Map<string, HabitationSummary>();

    habList.forEach((hab) => {
      const code = hab.id.replace(/^hab_/, "");
      habByCode.set(code, hab);
      habByName.set(hab.name.toLowerCase().trim(), hab);
    });

    const enrichedFeatures = geoJson.features.map((feature) => {
      const props = feature.properties || {};
      const vcode = String(props.village_code || "");
      const vname = String(props.village_name || props.village || "")
        .toLowerCase()
        .trim();

      const matchedHab = habByCode.get(vcode) || habByName.get(vname);

      return {
        ...feature,
        properties: {
          ...props,
          habitation_id: matchedHab ? matchedHab.id : null,
          habitation_name: matchedHab ? matchedHab.name : props.village_name || props.village,
          current_risk: matchedHab ? matchedHab.current_risk : null,
          priority: matchedHab ? matchedHab.priority : "Standard",
          risk_percent: matchedHab ? `${(matchedHab.current_risk * 100).toFixed(0)}%` : null,
        },
      };
    });

    return {
      ...geoJson,
      features: enrichedFeatures,
    };
  };

  // Initialize MapLibre map and load village polygon GeoJSON layer
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

    newMap.addControl(new maplibregl.NavigationControl(), "top-right");

    const setupMapLayers = async () => {
      try {
        const response = await fetch("/data/wayanad_village_boundaries.geojson");
        if (!response.ok) return;

        const data: GeoJSON.FeatureCollection = await response.json();
        rawGeoJson.current = data;

        const enrichedData = enrichGeoJson(data, habitations);

        if (!newMap.getSource("wayanad-villages")) {
          newMap.addSource("wayanad-villages", {
            type: "geojson",
            data: enrichedData,
          });

          // Data-driven polygon fill layer using MapLibre step expression
          newMap.addLayer({
            id: "wayanad-villages-fill",
            type: "fill",
            source: "wayanad-villages",
            paint: {
              "fill-color": [
                "case",
                ["==", ["get", "current_risk"], null],
                RISK_COLORS.NO_DATA,
                [
                  "step",
                  ["get", "current_risk"],
                  RISK_COLORS.LOWER,    // < 0.50 Lower risk
                  0.5,
                  RISK_COLORS.ELEVATED, // 0.50 - 0.7499 Elevated risk
                  0.75,
                  RISK_COLORS.HIGH,     // >= 0.75 High risk
                ],
              ],
              "fill-opacity": 0.45,
            },
          });

          // Polygon boundary outline layer
          newMap.addLayer({
            id: "wayanad-villages-outline",
            type: "line",
            source: "wayanad-villages",
            paint: {
              "line-color": "#1e293b",
              "line-width": 1.5,
              "line-opacity": 0.7,
            },
          });

          // Polygon hover cursor
          newMap.on("mouseenter", "wayanad-villages-fill", () => {
            newMap.getCanvas().style.cursor = "pointer";
          });

          newMap.on("mouseleave", "wayanad-villages-fill", () => {
            newMap.getCanvas().style.cursor = "";
          });

          // Polygon click event -> select habitation and show popup
          newMap.on("click", "wayanad-villages-fill", (e) => {
            const feature = e.features?.[0];
            if (!feature) return;

            const props = feature.properties;
            const habId = props?.habitation_id;
            const habName = props?.habitation_name || "Habitation";
            const riskVal = typeof props?.current_risk === "number" ? props.current_risk : null;
            const priorityVal = props?.priority || "Standard";

            if (habId) {
              onSelect?.(habId);
              router.push(`/habitations?id=${habId}`);
            }

            if (e.lngLat) {
              const category = classifyRisk(riskVal);
              const riskDisplay = riskVal !== null ? `${(riskVal * 100).toFixed(0)}%` : "Unavailable";

              new maplibregl.Popup({ offset: 15, closeButton: true })
                .setLngLat(e.lngLat)
                .setHTML(`
                  <div style="min-width: 170px; padding: 2px;">
                    <div style="font-size: 15px; font-weight: 600; color: #0f172a;">
                      ${habName}
                    </div>

                    <div style="margin-top: 8px; font-size: 13px; color: #475569;">
                      Current Risk:
                      <strong style="color: #0f172a;">
                        ${riskDisplay} (${category.label})
                      </strong>
                    </div>

                    <div style="margin-top: 4px; font-size: 13px; color: #475569;">
                      Priority:
                      <strong style="color: #0f172a;">
                        ${priorityVal}
                      </strong>
                    </div>
                  </div>
                `)
                .addTo(newMap);
            }
          });
        }
      } catch (err) {
        console.error("Failed to load or color village boundaries GeoJSON:", err);
      }
    };

    newMap.on("load", setupMapLayers);

    map.current = newMap;

    return () => {
      markers.current.forEach((marker) => marker.remove());
      markers.current = [];

      newMap.remove();
      map.current = null;
    };
  }, []);

  // Synchronize GeoJSON source and point markers when habitations prop updates
  useEffect(() => {
    const currentMap = map.current;

    if (!currentMap || habitations.length === 0) {
      return;
    }

    // Update GeoJSON source data with current habitations risk
    if (rawGeoJson.current && currentMap.getSource("wayanad-villages")) {
      const enriched = enrichGeoJson(rawGeoJson.current, habitations);
      const source = currentMap.getSource("wayanad-villages") as maplibregl.GeoJSONSource;
      source.setData(enriched);
    }

    const addMarkers = () => {
      markers.current.forEach((marker) => marker.remove());
      markers.current = [];

      habitations.forEach((habitation) => {
        const riskCategory = classifyRisk(habitation.current_risk);
        const markerColor = riskCategory.color;
        const isSelected = selectedId === habitation.id;

        const markerElement = document.createElement("div");

        markerElement.style.position = "relative";
        markerElement.style.width = "18px";
        markerElement.style.height = "18px";
        markerElement.style.borderRadius = "50%";
        markerElement.style.backgroundColor = markerColor;
        markerElement.style.border = isSelected
          ? "3px solid #0f172a"
          : "3px solid white";
        markerElement.style.boxShadow = "0 2px 6px rgba(0,0,0,0.35)";
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
        label.style.boxShadow = "0 1px 4px rgba(0,0,0,0.2)";
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
                ${(habitation.current_risk * 100).toFixed(0)}% (${riskCategory.label})
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
          .setLngLat([habitation.longitude, habitation.latitude])
          .setPopup(popup)
          .addTo(currentMap);

        markerElement.addEventListener("click", (e) => {
          e.stopPropagation(); // Prevent duplicate trigger from underlying polygon
          onSelect?.(habitation.id);

          currentMap.flyTo({
            center: [habitation.longitude, habitation.latitude],
            zoom: 12,
            duration: 800,
          });

          router.push(`/habitations?id=${habitation.id}`);
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