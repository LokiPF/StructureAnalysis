import configparser

import numpy as np

from Logger import Logger
from __structs__ import LoadCase, Parameters, Panel, LoadsInPlane, LoadsStringers, Stringer, IO
from io_handler import read_config, parse_excel

logger = Logger('main').logger


# FIXME: Check if can be removed
# def get_parameters() -> Parameters:
#     logger.info('Reading config file')
#     config = configparser.ConfigParser()
#     config.read('config.ini')
#     sigma_ul = config['PARAMETERS']['sigma_ul']
#     sigma_yield = config['PARAMETERS']['sigma_yield']
#     nu = config['PARAMETERS']['nu']
#     return Parameters(sigma_ul=float(sigma_ul), sigma_yield=float(sigma_yield), nu=float(nu))


def calc_buckling_factors(params: Parameters, sigma_y: float, sigma_x: float) -> [float,
                                                                                                                 float]:
    """Function to minimize the stress and calculate the number of halve waves in x- and y-direction"""
    alpha = params.a / params.b
    beta = sigma_y / sigma_x
    min_sigma = -1
    k_biax = 0
    for m in range(1, 10):
        for n in range(1, 10):
            k_sigma = np.square(np.square(m) + np.square(n * alpha)) / (
                        np.square(alpha) * (np.square(m) + beta * np.square(n * alpha)))
            sigma_crit = k_sigma * params.sigma_e
            if np.abs(sigma_crit) < np.abs(min_sigma) or min_sigma == -1:
                min_sigma = sigma_crit
                k_biax = k_sigma
    if alpha < 1:
        k_tau = 4 + 5.34 / np.square(alpha)
    else:
        k_tau = 5.34 + 4 / np.square(alpha)
    if np.isnan(k_biax):
        breakpoint()
    return [k_biax, k_tau]


def calc_avg_sigma_panel(load_cases: [LoadCase], params: Parameters) -> Panel:
    for load_case in load_cases:
        for i in range(5):
            panel = load_case.LoadsInPlane[i * 6:i * 6 + 6]
            avg_sigma = avg_panel(panel)
            buckling_f = calc_buckling_factors(params, avg_sigma[1], avg_sigma[0])
            R_biax = np.abs(buckling_f[0] * params.sigma_e / avg_sigma[0])
            R_shear = np.abs(buckling_f[1] * params.sigma_e / avg_sigma[1])
            R_combined = np.abs(1 / (1 / R_biax + np.square(1 / R_shear)))
            load_case.Panels.append(
                Panel(avg_xx=avg_sigma[0], avg_yy=avg_sigma[1], avg_xy=avg_sigma[2], k_biax=buckling_f[0],
                      k_tau=buckling_f[1], reserve_factor=R_combined))


def avg_panel(panel: LoadsInPlane):
    numerator_xx, numerator_yy, numerator_xy = 0, 0, 0
    for p in panel:
        numerator_xx += p.xx
        numerator_yy += p.yy
        numerator_xy += p.xy
    return numerator_xx / len(panel), numerator_yy / len(panel), numerator_xy / len(panel)


def avg_stringer(stringer: LoadsStringers):
    numerator = 0
    for s in stringer:
        numerator += s.stress
    return numerator / len(stringer)


def calc_avg_sigma_combined(load_cases: [LoadCase], E):
    for load_case in load_cases:
        for i in range(4):
            stringer = load_case.LoadsStringers[i * 3:i * 3 + 3]
            panel = load_case.LoadsInPlane[i * 6 + 3:i * 6 + 9]
            avg_stringer_xx = avg_stringer(stringer) * 3 * 56800
            avg_sigma_panel = avg_panel(panel)[0] * 6 * 160000
            sigma_combined = (avg_stringer_xx + avg_sigma_panel) / (56800 * 3 + 160000 * 6)
            sigma_crip = sigma_combined - 1 / E * np.square(sigma_combined / (2 * np.pi)) * np.square(115.4074149)
            load_case.Stringers.append(
                Stringer(sigma_axial=sigma_combined, sigma_crip=sigma_crip, reserve_factor=sigma_crip / sigma_combined))


if __name__ == '__main__':
    load_cases, io, parameters = read_config()
    # parameters = get_parameters()
    calc_avg_sigma_panel(load_cases, parameters)
    calc_avg_sigma_combined(load_cases, 64744.31)
    parse_excel(io, load_cases)
    pass
