"""
ROI Engine for Digital Twin Simulation Platform.

Computes financial metrics and ROI from KPIs and configuration.
"""

from typing import Dict


class ROIEngine:
    """
    Computes financial metrics and return on investment.

    All financial calculations are based on KPIs and configuration.
    """

    def __init__(self, kpis: dict, config: dict):
        """
        Initialize ROI engine with KPIs and configuration.

        Args:
            kpis: Dictionary containing operational KPIs:
                - throughput: int
                - utilization: float
            config: Configuration dictionary containing:
                - "revenue_per_swap": float (revenue per completed swap)
                - "charger_energy_cost": float (total energy cost)
                - "station_staff_cost": float (total staff cost)
                - "battery_depreciation_cost": float (total battery depreciation)
                - "infra_maintenance_cost": float (total infrastructure maintenance)
                - "capital_cost": float (total capital investment)
        """
        self.kpis = kpis
        self.config = config

        # TODO: Add validation for required config keys
        # TODO: Add caching for computed metrics

    def compute(self) -> dict:
        """
        Compute all financial metrics.

        Returns:
            Dictionary containing financial metrics:
                - revenue: float
                - operational_cost: float
                - net_profit: float
                - roi: float
        """
        revenue = self._compute_revenue()
        operational_cost = self._compute_operational_cost()
        net_profit = self._compute_net_profit(revenue, operational_cost)
        roi = self._compute_roi(net_profit)

        return {
            "revenue": revenue,
            "operational_cost": operational_cost,
            "net_profit": net_profit,
            "roi": roi
        }

    def _compute_revenue(self) -> float:
        """
        Compute total revenue from completed swaps.

        Returns:
            Total revenue in currency units
        """
        throughput = self.kpis.get("throughput", 0)
        revenue_per_swap = self.config.get("revenue_per_swap", 0.0)

        return throughput * revenue_per_swap

    def _compute_operational_cost(self) -> float:
        """
        Compute total operational costs.

        Returns:
            Total operational cost in currency units
        """
        charger_energy_cost = self.config.get("charger_energy_cost", 0.0)
        station_staff_cost = self.config.get("station_staff_cost", 0.0)
        battery_depreciation_cost = self.config.get("battery_depreciation_cost", 0.0)
        infra_maintenance_cost = self.config.get("infra_maintenance_cost", 0.0)

        return (
            charger_energy_cost +
            station_staff_cost +
            battery_depreciation_cost +
            infra_maintenance_cost
        )

    def _compute_net_profit(self, revenue: float, operational_cost: float) -> float:
        """
        Compute net profit.

        Args:
            revenue: Total revenue
            operational_cost: Total operational cost

        Returns:
            Net profit in currency units
        """
        return revenue - operational_cost

    def _compute_roi(self, net_profit: float) -> float:
        """
        Compute return on investment percentage.

        Args:
            net_profit: Net profit value

        Returns:
            ROI as a percentage (0.0 to 100.0)
        """
        capital_cost = self.config.get("capital_cost", 0.0)

        if capital_cost <= 0:
            return 0.0

        roi_percentage = (net_profit / capital_cost) * 100.0
        return roi_percentage

    def snapshot(self) -> dict:
        """
        Create a snapshot of computed financial metrics.

        Returns:
            Dictionary containing all financial metrics
        """
        return self.compute()
