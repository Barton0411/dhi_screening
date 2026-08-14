import unittest

import pandas as pd

from mastitis_monitoring import MastitisMonitoringCalculator


class ChronicInfectionProportionTest(unittest.TestCase):
    def test_denominator_uses_all_current_month_cattle(self):
        calculator = MastitisMonitoringCalculator(scc_threshold=20.0)
        calculator.monthly_data = {
            '2026-05': pd.DataFrame({
                'management_id_standardized': ['1', '2', '3'],
                'somatic_cell_count': [30.0, 10.0, 30.0],
            }),
            '2026-06': pd.DataFrame({
                'management_id_standardized': ['1', '2', '4', '5'],
                'somatic_cell_count': [35.0, 25.0, 10.0, 15.0],
            }),
        }

        result = calculator._calculate_chronic_infection_proportion(
            '2026-05', '2026-06'
        )

        self.assertEqual(result['numerator'], 1)
        self.assertEqual(result['denominator'], 4)
        self.assertEqual(result['overlap_count'], 2)
        self.assertEqual(result['value'], 25.0)
        self.assertIn('2026-06月参测牛头数(4)', result['formula'])
        self.assertNotIn('重叠牛只', result['formula'])


if __name__ == '__main__':
    unittest.main()
