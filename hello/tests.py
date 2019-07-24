"""
Test module for the sample application.
"""

import unittest

from hello.app import get_country_from_ip
from hello.validator import HeaderValidator


class TestHello(unittest.TestCase):
    """
        Tests if the validation of the headers being stored passes the simple validation rules.
        Tests the country lookup logic.
    """

    def setUp(self):
        """ Sets up the validator instance """
        self.validator = HeaderValidator()

    def test_geoip_lookup(self):
        """ Tests the geoip module of the application """
        country_name = "United States"
        country = get_country_from_ip("17.0.0.1")
        self.assertEqual(country, country_name)

    def test_invalid_headers(self):
        """" Tests whether a given colon separated header is valid """
        valid_headers = [
            'Expires: Tue, 12 Feb 2019 16:07:23 GMT',
            'X-XSS-Protection: 0'
        ]

        invalid_headers = [
            "\n\r",
            "Authentication:"
        ]

        for header in invalid_headers:
            self.assertFalse(self.validator.is_valid(header))

        for header in valid_headers:
            self.assertTrue(self.validator.is_valid(header))


if __name__ == '__main__':
    unittest.main()
