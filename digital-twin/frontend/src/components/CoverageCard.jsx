
import React, { useEffect, useState } from 'react';
import { Card, Table, Progress, Button, Alert } from 'antd';
import { AreaChartOutlined, ReloadOutlined } from '@ant-design/icons';
import { simulationAPI } from '../services/api';

const CoverageCard = ({ scenarioConfig }) => {
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);

    const fetchCoverage = async () => {
        setLoading(true);
        setError(null);
        try {
            // Need to pass full city config
            // If scenarioConfig doesn't have it (e.g. initial load), we might fail
            if (!scenarioConfig?.city_config) {
                // Try fetching default if no scenario loaded
                const res = await fetch('/city_graph_lucknow.json');
                const cityConfig = await res.json();
                const result = await simulationAPI.getCoverage({ city_config: cityConfig });
                setData(result);
            } else {
                const result = await simulationAPI.getCoverage(scenarioConfig);
                setData(result);
            }
        } catch (err) {
            console.error(err);
            setError("Failed to analyze coverage");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchCoverage();
    }, [scenarioConfig]);

    const columns = [
        {
            title: 'Zone',
            dataIndex: 'zone',
            key: 'zone',
            render: (text) => <span style={{ textTransform: 'capitalize' }}>{text.replace(/_/g, ' ')}</span>
        },
        {
            title: 'Coverage',
            dataIndex: 'score',
            key: 'score',
            render: (score) => (
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Progress
                        percent={score}
                        size="small"
                        status={score < 60 ? 'exception' : score < 80 ? 'active' : 'success'}
                        strokeColor={score < 60 ? '#ff4d4f' : score < 80 ? '#faad14' : '#52c41a'}
                    />
                </div>
            )
        }
    ];

    const tableData = data ? Object.entries(data.zone_coverage).map(([zone, score]) => ({
        key: zone,
        zone,
        score
    })) : [];

    return (
        <Card
            title={<span><AreaChartOutlined /> Network Health & Coverage</span>}
            extra={<Button icon={<ReloadOutlined />} onClick={fetchCoverage} loading={loading} type="text" />}
            style={{ marginTop: 24 }}
        >
            {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 16 }} />}

            {data && (
                <div style={{ textAlign: 'center', marginBottom: 24 }}>
                    <div style={{ fontSize: 12, color: '#8c8c8c' }}>OVERALL CITY SCORE</div>
                    <div style={{ fontSize: 32, fontWeight: 'bold', color: data.overall_score >= 80 ? '#52c41a' : '#faad14' }}>
                        {data.overall_score}%
                    </div>
                </div>
            )}

            <Table
                dataSource={tableData}
                columns={columns}
                pagination={false}
                size="small"
                loading={loading}
            />

            {data && data.underserved_zones.length > 0 && (
                <Alert
                    message="Optimization Opportunity"
                    description={`Low coverage detected in: ${data.underserved_zones.map(z => z.replace(/_/g, ' ')).join(', ')}.`}
                    type="warning"
                    showIcon
                    style={{ marginTop: 16 }}
                />
            )}
        </Card>
    );
};

export default CoverageCard;
