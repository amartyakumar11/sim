/**
 * CityVisualization Page: Digital Twin City View
 * 
 * Simplified version for debugging - shows basic content first
 */

import React, { useState, useEffect } from 'react';
import CityCanvas from '../components/CityCanvas';

const CityVisualization = () => {
    const [debug, setDebug] = useState('Loading...');

    useEffect(() => {
        setDebug('Page mounted successfully!');
    }, []);

    return (
        <div style={styles.page}>
            <header style={styles.header}>
                <h1 style={styles.title}>Digital Twin Visualization</h1>
                <p style={styles.subtitle}>
                    City view with zone pressure analysis and rider journeys
                </p>
                <p style={{ color: '#4caf50', fontWeight: 'bold' }}>{debug}</p>
            </header>

            <main style={styles.main}>
                <CityCanvas />
            </main>

            <footer style={styles.footer}>
                <p style={styles.footerText}>
                    Read-only visualization • Data from simulation observability artifacts
                </p>
            </footer>
        </div>
    );
};

const styles = {
    page: {
        minHeight: '100vh',
        backgroundColor: '#f5f5f5',
        display: 'flex',
        flexDirection: 'column'
    },
    header: {
        backgroundColor: 'white',
        borderBottom: '1px solid #e0e0e0',
        padding: '20px',
        textAlign: 'center'
    },
    title: {
        margin: '0 0 10px 0',
        color: '#1976D2',
        fontSize: '32px'
    },
    subtitle: {
        margin: 0,
        color: '#666',
        fontSize: '16px'
    },
    main: {
        flex: 1,
        padding: '20px',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'flex-start'
    },
    footer: {
        backgroundColor: 'white',
        borderTop: '1px solid #e0e0e0',
        padding: '15px',
        textAlign: 'center'
    },
    footerText: {
        margin: 0,
        color: '#999',
        fontSize: '13px'
    }
};

export default CityVisualization;
