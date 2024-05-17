from typing import NamedTuple


class LoadsInPlane(NamedTuple):
    e_id: int
    xx: float
    yy: float
    xy: float
    von_Mises: float
    reserve_factor: float


class LoadsStringers(NamedTuple):
    e_id: int
    stress: float
    reserve_factor: float


class Panel(NamedTuple):
    avg_xx: float
    avg_yy: float
    avg_xy: float
    k_biax: float
    k_tau: float
    reserve_factor: float = 0


class Stringer(NamedTuple):
    sigma_axial: float
    sigma_crip: float
    reserve_factor: float = 0


class LoadCase(NamedTuple):
    LoadsInPlane: list[LoadsInPlane]
    LoadsStringers: list[LoadsStringers]
    Panels: list[Panel]
    Stringers: list[Stringer]


class Parameters(NamedTuple):
    sigma_ul: float
    sigma_yield: float
    nu: float
    sigma_e: float

class IO(NamedTuple):
    output_file: str = ''
