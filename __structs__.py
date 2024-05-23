from typing import NamedTuple

import numpy as np


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


class Geometric(NamedTuple):
    I: float
    r_gyr: float
    lamda: float
    lamda_crit: float
    sigma_cr: float


class Stringer(NamedTuple):
    sigma_axial: float
    sigma_crip: float
    reserve_factor: float = 0
    geometrics: list[Geometric] = []


class LoadCase(NamedTuple):
    LoadsInPlane: list[LoadsInPlane]
    LoadsStringers: list[LoadsStringers]
    Panels: list[Panel]
    Stringers: list[Stringer]


class Parameters(NamedTuple):
    sigma_ul: float
    sigma_yield: float
    mu: float
    a: float
    b: float
    t: float
    stringer_base_w: float
    stringer_base_t: float
    stringer_height: float
    stringer_neck_width: float
    E: float
    sigma_e: float
    sf: float = 1.5


class IO(NamedTuple):
    output_file: str = ''
    sheet_name_output: str = ''
    delimiter: str = ''
