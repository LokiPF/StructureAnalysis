import configparser

import numpy as np

from Logger import Logger
from __structs__ import LoadCase, Parameters, Panel, LoadsInPlane, LoadsStringers, Stringer, IO, Geometric
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
            R_biax = np.abs(buckling_f[0] * params.sigma_e / (params.sf * avg_sigma[0]))
            R_shear = np.abs(buckling_f[1] * params.sigma_e / (params.sf * avg_sigma[2]))
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


def calc_avg_sigma_combined(load_cases: [LoadCase], params: Parameters):
    for load_case in load_cases:
        for i in range(4):
            stringer = load_case.LoadsStringers[i * 3:i * 3 + 3]
            panel = load_case.LoadsInPlane[i * 6 + 3:i * 6 + 9]
            avg_stringer_xx = avg_stringer(stringer) * 3 * 56800
            avg_sigma_panel = avg_panel(panel)[0] * 6 * 160000
            sigma_combined = (avg_stringer_xx + avg_sigma_panel) / (56800 * 3 + 160000 * 6)
            # sigma_crip = params.sigma_yield - 1 / params.E * np.square(params.sigma_yield / (2 * np.pi)) * np.square(
            #     115.4074149)
            # b_1_1 = params.stringer_base_w / 2 - (params.stringer_neck_width / 2) * (
            #             0.25 * params.stringer_neck_width / params.stringer_base_t)
            b_1_2 = params.stringer_height - params.stringer_base_t / 2 * (
                        2 - 0.5 * params.stringer_neck_width / params.stringer_base_t)
            # x_1 = b_1_1 / params.stringer_base_t * np.sqrt(params.sigma_yield / (0.41 * params.E))
            x_2 = b_1_2 / params.stringer_neck_width * np.sqrt(params.sigma_yield / (0.41 * params.E))
            if x_2 <= 1.095:
                alpha_2 = 1.4 - 0.628 * x_2
            elif x_2 <= 1.633:
                alpha_2 = 0.78 / x_2
            else:
                alpha_2 = 0.69 / np.power(x_2, 0.75)
            sigma_crip = alpha_2 * params.sigma_yield
            if params.sigma_yield < sigma_crip:
                R_f = params.sigma_yield / sigma_combined
            else:
                R_f = sigma_crip / sigma_combined
            I, r_gyr, lamda = calc_lamda(params)
            lamda_crit = calc_crit_lamda(Stringer(sigma_combined, sigma_crip, 0), params) # pseudo stringer
            if lamda < lamda_crit:
                sigma_cr = params.sigma_yield - 1/params.E * np.square(params.sigma_yield / (2*np.pi)) * np.square(lamda)
            else:
                sigma_cr = np.square(np.pi) * params.E / np.square(lamda)
            R_f = sigma_cr / (params.sf * sigma_combined)
            load_case.Stringers.append(
                Stringer(sigma_axial=sigma_combined, sigma_crip=sigma_crip, reserve_factor=np.abs(R_f)))


def calc_crit_lamda(stringer: Stringer, params: Parameters):
    if np.abs(stringer.sigma_crip) < np.abs(params.sigma_yield):
        lamda_crit = np.sqrt(2 * np.square(np.pi) * params.E / np.abs(stringer.sigma_crip))
    else:
        lamda_crit = np.sqrt(2 * np.square(np.pi) * params.E / params.sigma_yield)
    return lamda_crit


def calc_lamda(params: Parameters):
    A_skin = params.t * params.b
    A_stringer_base = params.stringer_base_w * params.stringer_base_t
    A_stringer_neck = (params.stringer_height - params.stringer_base_t) * params.stringer_neck_width
    A = A_skin + A_stringer_base + A_stringer_neck
    z_bar_numerator = -params.t / 2 * A_skin + params.stringer_base_t / 2 * A_stringer_base + (
            params.stringer_base_t + (params.stringer_height - params.stringer_base_t) / 2) * A_stringer_neck
    z_bar = z_bar_numerator / A
    I_skin = np.power(params.t, 3) * params.b / 12 + A_skin * np.square(-params.t / 2 - z_bar)
    I_stringer_base = np.power(params.stringer_base_t, 3) * params.stringer_base_w / 12 + A_stringer_base * np.square(
        params.stringer_base_t / 2 - z_bar)
    I_stringer_neck = np.power(params.stringer_height - params.stringer_base_t,
                               3) * params.stringer_neck_width / 12 + A_stringer_neck * np.square(
        params.stringer_base_t + (params.stringer_height - params.stringer_base_t) / 2 - z_bar)
    I = I_skin + I_stringer_base + I_stringer_neck
    r_gyr = np.sqrt(I / A)
    lamda = params.a / r_gyr
    return I, r_gyr, lamda


def calc_geoms(params: Parameters, load_cases: [LoadCase], flag = 0):
    I, r_gyr, lamda = calc_lamda(params)
    if flag:
        return lamda
    for load_case in load_cases:
        for stringer in load_case.Stringers:
            lamda_crit = calc_crit_lamda(stringer, params)
            sigma_cr = np.square(np.pi) * params.E / np.square(lamda)
            stringer.geometrics.append(Geometric(I=I, r_gyr=r_gyr, lamda=lamda, lamda_crit=lamda_crit, sigma_cr=sigma_cr))

if __name__ == '__main__':
    load_cases, io, parameters = read_config()
    calc_avg_sigma_panel(load_cases, parameters)
    calc_avg_sigma_combined(load_cases, parameters)
    calc_geoms(parameters, load_cases)
    parse_excel(io, load_cases)
    pass
