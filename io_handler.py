import configparser

import openpyxl
import pandas as pd

from Logger import Logger
from __structs__ import LoadCase, LoadsInPlane, LoadsStringers, IO, Parameters

logger = Logger('read_excel').logger


def read_config() -> [LoadCase]:
    logger.info('Reading config file')
    config = configparser.ConfigParser()
    config.read('config.ini')
    in_plane_stresses = config['INPUT']['in_plane_stresses']
    axial_stringer_stresses = config['INPUT']['axial_stringer_stresses']
    sigma_ul = float(config['PARAMETERS']['sigma_ul'])
    io = IO(config['OUTPUT']['output_file'])
    sigma_ul = config['PARAMETERS']['sigma_ul']
    sigma_yield = config['PARAMETERS']['sigma_yield']
    nu = config['PARAMETERS']['nu']
    parameters = Parameters(sigma_ul=float(sigma_ul), sigma_yield=float(sigma_yield), nu=float(nu), sigma_e=6.021038057)
    return read_excel(in_plane_stresses, axial_stringer_stresses, sigma_ul=float(sigma_ul)), io, parameters


def read_excel(in_plane_stresses: str, axial_stringer_stresses: str, sigma_ul: float) -> [LoadCase]:
    logger.info('Reading excel file')
    ips = pd.read_excel(in_plane_stresses)
    ass = pd.read_excel(axial_stringer_stresses)
    load_cases = [LoadCase([], [], [], []) for _ in range(3)]

    k = 10
    j = 10
    for i, load_case in enumerate(load_cases):
        while ips.iat[k, 2] == i + 1:
            load_case.LoadsInPlane.append(
                LoadsInPlane(e_id=ips.iat[k, 0], xx=1.5 * ips.iat[k, 5], yy=1.5 * ips.iat[k, 7], xy=1.5 * ips.iat[k, 6],
                             von_Mises=1.5 * ips.iat[k, 8], reserve_factor=sigma_ul / (1.5 * float(ips.iat[k, 8]))))
            k += 1
            if k > len(ips) - 1:
                break
        while ass.iat[j, 2] == i + 1:
            load_case.LoadsStringers.append(LoadsStringers(e_id=ass.iat[j, 0], stress=1.5 * ass.iat[j, 4],
                                                           reserve_factor=sigma_ul / (1.5 * ass.iat[j, 4])))
            j += 1
            if j > len(ass) - 1:
                break
    logger.info('Finished reading excel file')
    return load_cases


def parse_excel(io: IO, load_cases: [LoadCase]):
    wb = openpyxl.load_workbook(io.output_file)
    ws = wb.get_sheet_by_name('in')
    column = 2
    for i, load_case in enumerate(load_cases):
        row = 17
        for k, load in enumerate(load_case.LoadsInPlane):
            cellref = ws.cell(row=row + k, column=column)
            cellref.value = load.reserve_factor
        column += 3
    wb.save(io.output_file)
    logger.info('Finished parsing excel file')