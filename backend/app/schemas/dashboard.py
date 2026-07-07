"""Dashboard aggregate schemas."""

from typing import Any
from pydantic import BaseModel


class SectorSnapshot(BaseModel):
    sector: str
    count: int
    capacity: int
    density: float
    status: str   # NORMAL | WARNING | CRITICAL


class ParkingSnapshot(BaseModel):
    lot_name: str
    total_spots: int
    occupied_spots: int
    occupancy_percentage: int
    status: str


class TransportSnapshot(BaseModel):
    vehicle_id: str
    route_name: str
    type: str
    status: str
    occupancy_percentage: int
    latitude: float
    longitude: float
    current_stop: str | None


class EnergySnapshot(BaseModel):
    grid_zone: str
    active_power_kw: float
    load_percentage: float


class CarbonSnapshot(BaseModel):
    total_kg: float
    by_category: dict[str, float]


class IncidentSummary(BaseModel):
    total: int
    active: int
    mitigating: int
    resolved: int
    critical: int


class DashboardResponse(BaseModel):
    """Complete real-time dashboard payload."""
    timestamp: str
    twin_status: Any
    incidents: IncidentSummary
    sectors: list[SectorSnapshot]
    parking: list[ParkingSnapshot]
    transport: list[TransportSnapshot]
    energy: list[EnergySnapshot]
    carbon: CarbonSnapshot
    unread_notifications: int
