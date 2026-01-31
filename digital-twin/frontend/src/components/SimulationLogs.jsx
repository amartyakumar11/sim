import React, { useMemo, useEffect, useRef } from 'react';
import { AlertCircle, ArrowRight, BatteryCharging, AlertTriangle } from 'lucide-react';

/**
 * SimulationLogs Component
 * 
 * Displays a scrolling log of simulation events synced to the playback time.
 * Since we don't have the raw event stream in the frontend, we reconstruct
 * key events (Stockouts, Redirections) from the station timelines and rider traces.
 */
const SimulationLogs = ({
    currentMinute,
    stationTimelines = {},
    riderTraces = {},
    recommendations = []
}) => {
    const scrollRef = useRef(null);

    // 1. Reconstruct Event Stream
    const events = useMemo(() => {
        const allEvents = [];

        // A. Station Events (Stockouts)
        Object.entries(stationTimelines).forEach(([stationId, data]) => {
            const timeline = data.timeline || [];
            // Track when stockout starts to avoid spamming every minute
            let inStockout = false;

            timeline.forEach(point => {
                if (point.inventory === 0 && !inStockout) {
                    allEvents.push({
                        minute: point.minute,
                        type: 'STOCKOUT',
                        stationId,
                        message: `Station ${stationId} ran out of batteries!`,
                        severity: 'high'
                    });
                    inStockout = true;
                } else if (point.inventory > 0) {
                    inStockout = false;
                }
            });
        });

        // B. Rider Events (Redirections)
        Object.values(riderTraces).forEach(rider => {
            // Check for redirections (if available)
            if (rider.redirections) {
                rider.redirections.forEach(redir => {
                    allEvents.push({
                        minute: redir.minute,
                        type: 'REDIRECT',
                        riderId: rider.rider_id,
                        fromStation: redir.from_station,
                        toStation: redir.to_station,
                        distance: redir.distance,
                        message: `Rider ${rider.rider_id} redirected from ${redir.from_station} to ${redir.to_station}`,
                        severity: 'medium'
                    });
                });
            }
        });

        // C. Recommendation Events
        if (recommendations) {
            recommendations.forEach(rec => {
                allEvents.push({
                    minute: rec.minute,
                    type: 'DEMAND_GAP',
                    riderId: rec.rider_id,
                    location: `${rec.lat.toFixed(4)}, ${rec.lon.toFixed(4)}`,
                    message: `Service failure at ${rec.lat.toFixed(4)}, ${rec.lon.toFixed(4)} - New Station Needed!`,
                    severity: 'critical'
                });
            });
        }

        // Sort by time
        return allEvents.sort((a, b) => a.minute - b.minute);
    }, [stationTimelines, riderTraces, recommendations]);

    // 2. Filter visible events based on current playback minute
    // We show events from [currentMinute - 30] to [currentMinute]
    const visibleEvents = useMemo(() => {
        if (currentMinute === null) return [];
        return events.filter(e => e.minute <= currentMinute && e.minute > currentMinute - 60);
    }, [events, currentMinute]);

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [visibleEvents]);

    if (!currentMinute) return null;

    return (
        <div style={styles.container}>
            <div style={styles.header}>
                <h3 style={styles.title}>Live Event Log</h3>
                <span style={styles.badge}>{visibleEvents.length} events (last hr)</span>
            </div>

            <div style={styles.logList} ref={scrollRef}>
                {visibleEvents.length === 0 ? (
                    <div style={styles.emptyState}>No critical events nearby</div>
                ) : (
                    visibleEvents.map((event, idx) => (
                        <div key={`${event.minute}-${idx}`} style={styles.eventItem}>
                            <div style={styles.eventTime}>{formatTime(event.minute)}</div>
                            <div style={styles.eventContent}>
                                <div style={styles.eventType}>
                                    {getIconForType(event.type)}
                                    <span style={{
                                        ...styles.typeText,
                                        color: getColorForType(event.type)
                                    }}>
                                        {event.type}
                                    </span>
                                </div>
                                <div style={styles.eventMessage}>{event.message}</div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

// Helpers
const formatTime = (minutes) => {
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
};

const getIconForType = (type) => {
    switch (type) {
        case 'STOCKOUT': return <BatteryCharging size={14} color="#ef4444" />;
        case 'REDIRECT': return <ArrowRight size={14} color="#f59e0b" />;
        case 'DEMAND_GAP': return <AlertTriangle size={14} color="#dc2626" />;
        default: return <AlertCircle size={14} color="#6b7280" />;
    }
};

const getColorForType = (type) => {
    switch (type) {
        case 'STOCKOUT': return '#ef4444';
        case 'REDIRECT': return '#f59e0b';
        case 'DEMAND_GAP': return '#dc2626';
        default: return '#6b7280';
    }
};

const styles = {
    container: {
        position: 'absolute',
        bottom: 32,
        left: 16,
        width: 320,
        maxHeight: 300,

        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderRadius: 12,
        boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        pointerEvents: 'auto', // ensure interaction
        zIndex: 1000
    },
    header: {
        padding: '12px 16px',
        borderBottom: '1px solid #e5e7eb',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: '#f9fafb'
    },
    title: {
        margin: 0,
        fontSize: 14,
        fontWeight: 'bold',
        color: '#1f2937'
    },
    badge: {
        fontSize: 11,
        color: '#6b7280',
        backgroundColor: '#e5e7eb',
        padding: '2px 6px',
        borderRadius: 10
    },
    logList: {
        flex: 1,
        overflowY: 'auto',
        padding: '8px 0',
        scrollBehavior: 'smooth'
    },
    eventItem: {
        display: 'flex',
        gap: 12,
        padding: '8px 16px',
        borderBottom: '1px solid #f3f4f6',
        fontSize: 13
    },
    eventTime: {
        color: '#9ca3af',
        fontFamily: 'monospace',
        fontSize: 11,
        marginTop: 2
    },
    eventContent: {
        flex: 1
    },
    eventType: {
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        marginBottom: 2
    },
    typeText: {
        fontWeight: 'bold',
        fontSize: 11
    },
    eventMessage: {
        color: '#374151',
        lineHeight: 1.4
    },
    emptyState: {
        padding: 20,
        textAlign: 'center',
        color: '#9ca3af',
        fontSize: 13,
        fontStyle: 'italic'
    }
};

export default SimulationLogs;
