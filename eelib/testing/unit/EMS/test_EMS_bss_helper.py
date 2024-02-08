"""
Unittest for bss helper of eELib

Author: elenia@TUBS
Copyright 2024 elenia
This file is part of eELib, which is free software under the terms of the GNU GPL Version 3.
"""

import unittest
import time
import eelib.core.control.EMS.EMS_bss_helper as bss_help


class TestEMS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        print(f"[START] {self.id()}")
        self.start = time.time()

    def tearDown(self):
        t = time.time() - self.start
        print(f"[END] {self.id()}: {t:.4f}")

    def test_bss_calc_balance(self):
        p_min = -2000
        p_max = 2000

        # for p_balance > 0
        p_balance = -1000
        p_set_bss = bss_help.bss_calc_balance(p_balance, p_max, p_min)
        self.assertAlmostEqual(p_set_bss, -p_balance)

        # for p_balance < 0
        p_balance = 1000
        p_set_bss = bss_help.bss_calc_balance(p_balance, p_max, p_min)
        self.assertAlmostEqual(p_set_bss, -p_balance)

    def test_bss_calc_e_bat(self):
        step_size = 900
        bss_full_id = "BSS_0"
        bss_self_discharge_step = 0.000007
        bss_e_bat_usable = 8000
        bss_soc_min = 0.05
        bss_discharge_efficiency_static = 0.95
        bss_charge_efficiency_static = 0.95

        # discharging
        bss_e_bat_forecast = 4000.0
        t = 0
        p_set_bss_forecast = {0: {bss_full_id: -8000}}

        self.assertAlmostEqual(
            bss_help.bss_calc_e_bat(
                t,
                step_size,
                bss_e_bat_forecast,
                p_set_bss_forecast,
                bss_full_id,
                bss_self_discharge_step,
                bss_e_bat_usable,
                bss_soc_min,
                bss_charge_efficiency_static,
                bss_discharge_efficiency_static,
            ),
            2099.9719999999998,
        )

        # charging
        bss_e_bat_forecast = 4000.0
        p_set_bss_forecast = {0: {bss_full_id: 8000}}
        self.assertAlmostEqual(
            bss_help.bss_calc_e_bat(
                t,
                step_size,
                bss_e_bat_forecast,
                p_set_bss_forecast,
                bss_full_id,
                bss_self_discharge_step,
                bss_e_bat_usable,
                bss_soc_min,
                bss_charge_efficiency_static,
                bss_discharge_efficiency_static,
            ),
            5899.972,
        )

    def test_bss_calc_p_limits(self):
        step_size = 900
        bss_full_id = "BSS_0"
        bss_e_bat_usable = {bss_full_id: 8000}
        bss_soc_min = {bss_full_id: 0.05}
        bss_discharge_efficiency_static = {bss_full_id: 0.95}
        bss_p_rated_discharge_max = {bss_full_id: -8000}
        bss_charge_efficiency_static = {bss_full_id: 0.95}
        bss_p_rated_charge_max = {bss_full_id: 8000}
        bss_e_bat_forecast = {bss_full_id: 4000}
        bss_self_discharge_step = {bss_full_id: 0.000007}

        p_max_bss_forecast, p_min_bss_forecast = bss_help.bss_calc_p_limits(
            step_size,
            bss_e_bat_forecast[bss_full_id],
            bss_soc_min[bss_full_id],
            bss_e_bat_usable[bss_full_id],
            bss_p_rated_charge_max[bss_full_id],
            bss_p_rated_discharge_max[bss_full_id],
            bss_discharge_efficiency_static[bss_full_id],
            bss_charge_efficiency_static[bss_full_id],
            bss_self_discharge_step[bss_full_id],
        )
        self.assertAlmostEqual(
            p_max_bss_forecast,
            bss_p_rated_charge_max[bss_full_id],
        )
        self.assertAlmostEqual(
            p_min_bss_forecast,
            bss_p_rated_discharge_max[bss_full_id],
        )

    def test_bss_set_energy_within_limit(self):
        bss_full_id = "BSS_0"
        bss_e_bat_usable = {bss_full_id: 8000}
        bss_soc_min = {bss_full_id: 0.05}

        # OVERCHARGE
        bss_e_bat_forecast = 8050
        bss_in_limit = bss_help.bss_set_energy_within_limit(
            bss_e_bat_forecast,
            bss_e_bat_usable[bss_full_id],
            bss_soc_min[bss_full_id],
        )
        self.assertAlmostEqual(bss_in_limit, bss_e_bat_usable[bss_full_id])

        # UNDERCHARGE
        bss_e_bat_forecast = (bss_e_bat_usable[bss_full_id] * bss_soc_min[bss_full_id]) - 50
        bss_in_limit = bss_help.bss_set_energy_within_limit(
            bss_e_bat_forecast,
            bss_e_bat_usable[bss_full_id],
            bss_soc_min[bss_full_id],
        )
        self.assertAlmostEqual(
            bss_in_limit,
            bss_e_bat_usable[bss_full_id] * bss_soc_min[bss_full_id],
        )


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEMS)
    unittest.TextTestRunner(verbosity=0).run(suite)
