"""
Module contains a simple header validator used to check for allowed characters in header inputs.
"""

class HeaderValidator:
    """
        Validates if a header has valid Name:Value values for the data presented from the browser.
    """

    def __init__(self):
        self.allowed_header_name_chars = []
        self.allowed_header_name_chars.extend(list(range(48, 58)))  # 0-9
        self.allowed_header_name_chars.extend(list(range(65, 91)))  # a-z
        self.allowed_header_name_chars.extend(list(range(97, 123)))  # A-Z
        self.allowed_header_name_chars.extend(
            [94, 95, 96, 124, 126])  # ^, _, `, |, ~
        self.allowed_header_name_chars.extend(
            [33, 35, 36, 37, 38, 39, 42, 43, 45, 46])  # !, #, $, %, &, ', *, +, -, .,

    def is_valid_value_character(self, char):
        """ Checks whether a header value character is valid """
        if char == 9:
            return True

        if char > 31 and char <= 255 and char != 127:
            return True

        return False

    def is_valid_header_value(self, value):
        """ Checks whether a header value is valid """
        characters = [ord(char) for char in value]
        for char in characters:
            if not self.is_valid_value_character(char):
                return False
        return True

    def is_valid_header_name(self, name):
        """ Checks whether a header name is valid """
        characters = [ord(char) for char in name]
        for char in characters:
            if char not in self.allowed_header_name_chars:
                return False
        return True

    def is_valid(self, header):
        """ Validates a header string """
        try:
            name, value = header.split(':', 1)
            name, value = name.strip(), value.strip()

            if name and value:
                return self.is_valid_header_name(
                    name) and self.is_valid_header_value(value)

        except ValueError:
            print("Error unpacking header values")

        return False
