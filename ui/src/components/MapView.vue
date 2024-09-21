<template>
  <div id="map"></div>
</template>

<script lang="ts">
import { defineComponent, onMounted } from 'vue';
import maplibregl from 'maplibre-gl';
import { getPathFromBackend } from '../services/backend';

export default defineComponent({
  name: 'MapView',
  setup() {
    let map: maplibregl.Map;
    let clickedCoordinates: [number, number][] = [];

    // Define the onClick function
    const onClick = (e: maplibregl.MapMouseEvent) => {
      const coords = [e.lngLat.lng, e.lngLat.lat] as [number, number];
      clickedCoordinates.push(coords);

      if (clickedCoordinates.length === 2) {
        const [start, end] = clickedCoordinates;
        
        getPathFromBackend(start, end).then((pathData) => {
          drawPathOnMap(map, pathData);
          clickedCoordinates = [];
        }).catch((error) => {
          console.error('Error fetching path:', error);
          clickedCoordinates = [];
        });
      }
    };

    const drawPathOnMap = (map: maplibregl.Map, pathData: any) => {
      const pathSourceId = 'pathSource';
      const pathLayerId = 'pathLayer';

      if (map.getSource(pathSourceId)) {
        map.removeLayer(pathLayerId);
        map.removeSource(pathSourceId);
      }

      map.addSource(pathSourceId, { type: 'geojson', data: pathData });
      map.addLayer({
        id: pathLayerId,
        type: 'line',
        source: pathSourceId,
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: { 'line-color': '#ff0000', 'line-width': 4 },
      });
    };

    onMounted(() => {
      const bounds = [
        [2.0, 41.3], // SW coordinates (longitude, latitude)
        [2.3, 41.5], // NE coordinates (longitude, latitude)
      ];

      map = new maplibregl.Map({
        container: 'map',
        style: '../../styles_jsons/alidade_smooth_dark.json',
        center: [2.1734, 41.3851],
        zoom: 6,
        maxBounds: bounds,
      });

      map.addControl(new maplibregl.NavigationControl());
      map.on('load', () => { map.resize(); });
      map.on('click', onClick);
    });

    return {};
  },
});
</script>

<style scoped>
#map {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
}
</style>
