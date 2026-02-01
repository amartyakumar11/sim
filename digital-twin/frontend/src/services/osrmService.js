/**
 * OSRM Route Service
 * 
 * Fetches real road routes from the free OSRM API.
 * Includes caching to avoid redundant API calls and rate limiting.
 * 
 * API: https://router.project-osrm.org/route/v1/driving/
 * Format: {startLng},{startLat};{endLng},{endLat}?overview=full&geometries=geojson
 */

// Cache for routes (key: "lat1,lon1->lat2,lon2")
const routeCache = new Map();

// Queue for pending requests (to implement rate limiting)
let requestQueue = [];
let isProcessingQueue = false;

/**
 * Generate cache key for a route
 */
function getCacheKey(from, to) {
    // Round to 5 decimal places to catch near-identical routes
    const round = (n) => Math.round(n * 100000) / 100000;
    return `${round(from.lat)},${round(from.lon)}->${round(to.lat)},${round(to.lon)}`;
}

/**
 * Process the request queue with rate limiting
 */
async function processQueue() {
    if (isProcessingQueue || requestQueue.length === 0) return;
    
    isProcessingQueue = true;
    
    while (requestQueue.length > 0) {
        const { from, to, resolve, reject } = requestQueue.shift();
        
        try {
            const route = await fetchRouteFromOSRM(from, to);
            resolve(route);
        } catch (error) {
            reject(error);
        }
        
        // Rate limiting: wait 100ms between requests
        if (requestQueue.length > 0) {
            await new Promise(r => setTimeout(r, 100));
        }
    }
    
    isProcessingQueue = false;
}

/**
 * Fetch route from OSRM API
 * @param {Object} from - { lat, lon }
 * @param {Object} to - { lat, lon }
 * @returns {Array} Array of [lat, lon] coordinates for the route
 */
async function fetchRouteFromOSRM(from, to) {
    // OSRM uses lng,lat format
    const url = `https://router.project-osrm.org/route/v1/driving/${from.lon},${from.lat};${to.lon},${to.lat}?overview=full&geometries=geojson`;
    
    const response = await fetch(url);
    
    if (!response.ok) {
        throw new Error(`OSRM API error: ${response.status}`);
    }
    
    const data = await response.json();
    
    if (data.code !== 'Ok' || !data.routes || data.routes.length === 0) {
        throw new Error('No route found');
    }
    
    // OSRM returns coordinates as [lng, lat], convert to [lat, lon] for Leaflet/MapLibre
    const coordinates = data.routes[0].geometry.coordinates;
    const latLonCoords = coordinates.map(([lng, lat]) => [lat, lng]);
    
    return {
        coordinates: latLonCoords,
        duration: data.routes[0].duration, // seconds
        distance: data.routes[0].distance, // meters
        // Keep original lng,lat format for GeoJSON rendering
        geoJsonCoordinates: coordinates
    };
}

/**
 * Get a route between two points
 * Uses cache if available, otherwise fetches from OSRM
 * 
 * @param {Object} from - { lat, lon }
 * @param {Object} to - { lat, lon }
 * @param {boolean} useQueue - Whether to use rate-limited queue (default: true)
 * @returns {Promise<Object>} Route data with coordinates
 */
export async function getRoute(from, to, useQueue = true) {
    const cacheKey = getCacheKey(from, to);
    
    // Check cache first
    if (routeCache.has(cacheKey)) {
        return routeCache.get(cacheKey);
    }
    
    // Return promise that will be resolved when route is fetched
    return new Promise((resolve, reject) => {
        if (useQueue) {
            // Add to queue for rate-limited processing
            requestQueue.push({ from, to, resolve, reject });
            processQueue();
        } else {
            // Direct fetch without queue
            fetchRouteFromOSRM(from, to)
                .then(route => {
                    routeCache.set(cacheKey, route);
                    resolve(route);
                })
                .catch(error => {
                    // Fallback to straight line
                    const fallbackRoute = createStraightLineRoute(from, to);
                    routeCache.set(cacheKey, fallbackRoute);
                    resolve(fallbackRoute);
                });
        }
    }).then(route => {
        routeCache.set(cacheKey, route);
        return route;
    }).catch(error => {
        console.warn(`OSRM route failed for ${cacheKey}, using fallback:`, error.message);
        const fallbackRoute = createStraightLineRoute(from, to);
        routeCache.set(cacheKey, fallbackRoute);
        return fallbackRoute;
    });
}

/**
 * Create a straight line fallback route
 */
function createStraightLineRoute(from, to) {
    // Calculate approximate distance using Haversine
    const R = 6371000; // Earth radius in meters
    const lat1 = from.lat * Math.PI / 180;
    const lat2 = to.lat * Math.PI / 180;
    const deltaLat = (to.lat - from.lat) * Math.PI / 180;
    const deltaLon = (to.lon - from.lon) * Math.PI / 180;
    
    const a = Math.sin(deltaLat / 2) ** 2 +
              Math.cos(lat1) * Math.cos(lat2) * Math.sin(deltaLon / 2) ** 2;
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    const distance = R * c;
    
    // Estimate duration at ~30 km/h average city speed
    const duration = distance / (30 * 1000 / 3600);
    
    return {
        coordinates: [[from.lat, from.lon], [to.lat, to.lon]],
        geoJsonCoordinates: [[from.lon, from.lat], [to.lon, to.lat]],
        duration,
        distance,
        isFallback: true
    };
}

/**
 * Prefetch routes for a list of station pairs
 * Useful for batch loading routes when simulation starts
 * 
 * @param {Array} pairs - Array of { from: {lat, lon}, to: {lat, lon} }
 * @returns {Promise<Map>} Map of cache keys to routes
 */
export async function prefetchRoutes(pairs) {
    const results = new Map();
    
    for (const { from, to } of pairs) {
        try {
            const route = await getRoute(from, to);
            results.set(getCacheKey(from, to), route);
        } catch (error) {
            console.warn('Failed to prefetch route:', error);
        }
    }
    
    return results;
}

/**
 * Interpolate position along a route based on progress (0-1)
 * 
 * @param {Array} coordinates - Array of [lat, lon] points
 * @param {number} progress - 0 to 1 (start to end)
 * @returns {Object} { lat, lon } interpolated position
 */
export function interpolateAlongRoute(coordinates, progress) {
    if (!coordinates || coordinates.length === 0) {
        return null;
    }
    
    if (coordinates.length === 1) {
        return { lat: coordinates[0][0], lon: coordinates[0][1] };
    }
    
    // Clamp progress
    progress = Math.max(0, Math.min(1, progress));
    
    if (progress === 0) {
        return { lat: coordinates[0][0], lon: coordinates[0][1] };
    }
    if (progress === 1) {
        const last = coordinates[coordinates.length - 1];
        return { lat: last[0], lon: last[1] };
    }
    
    // Calculate total route length
    let totalLength = 0;
    const segmentLengths = [];
    
    for (let i = 0; i < coordinates.length - 1; i++) {
        const [lat1, lon1] = coordinates[i];
        const [lat2, lon2] = coordinates[i + 1];
        const length = Math.sqrt((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2);
        segmentLengths.push(length);
        totalLength += length;
    }
    
    // Find the segment containing the target distance
    const targetDistance = progress * totalLength;
    let accumulatedDistance = 0;
    
    for (let i = 0; i < segmentLengths.length; i++) {
        const segmentLength = segmentLengths[i];
        
        if (accumulatedDistance + segmentLength >= targetDistance) {
            // Interpolate within this segment
            const segmentProgress = (targetDistance - accumulatedDistance) / segmentLength;
            const [lat1, lon1] = coordinates[i];
            const [lat2, lon2] = coordinates[i + 1];
            
            return {
                lat: lat1 + (lat2 - lat1) * segmentProgress,
                lon: lon1 + (lon2 - lon1) * segmentProgress
            };
        }
        
        accumulatedDistance += segmentLength;
    }
    
    // Fallback to last point
    const last = coordinates[coordinates.length - 1];
    return { lat: last[0], lon: last[1] };
}

/**
 * Get cached route count for debugging
 */
export function getCacheStats() {
    return {
        cachedRoutes: routeCache.size,
        pendingRequests: requestQueue.length
    };
}

/**
 * Clear the route cache
 */
export function clearCache() {
    routeCache.clear();
}

export default {
    getRoute,
    prefetchRoutes,
    interpolateAlongRoute,
    getCacheStats,
    clearCache
};
