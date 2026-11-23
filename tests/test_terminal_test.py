import unittest
from unittest.mock import patch
import tools.terminal_test as diagnostic


class TerminalTests(unittest.TestCase):
    def test_missing_values_do_not_turn_stopped_camera_into_fake_zero_fps(self):
        self.assertIsNone(diagnostic.summary([None,None]))
        self.assertEqual(diagnostic.summary([None,10.,20.])['mean'],15.)

    def test_throttle_flags_keep_current_and_historical_distinct(self):
        with patch('tools.terminal_test.subprocess.check_output',return_value='throttled=0x50000\n'):
            value=diagnostic.throttle()
        self.assertIn('undervoltage_since_boot',value['flags'])
        self.assertIn('throttled_since_boot',value['flags'])
        self.assertNotIn('throttled_now',value['flags'])


if __name__=='__main__':unittest.main()
