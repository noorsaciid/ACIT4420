"""Exceptions used by the CSV loading layer."""


class InvalidIdentifierError(ValueError):
    """Raised when an identifier has an invalid format."""

    def __init__(self, field, value, source, row_number):
        self.field = field
        self.value = value
        self.source = source
        self.row_number = row_number
        super().__init__(self._message())

    def _message(self):
        return "%s has invalid value %r" % (self.field, self.value)

    def as_record(self):
        return {"source": self.source, "row": self.row_number,
                "field": self.field, "reason": "invalid value %r" % self.value}


class InvalidRecordError(ValueError):
    """Raised when a CSV record cannot be accepted."""

    def __init__(self, field, reason, source, row_number):
        self.field = field
        self.reason = reason
        self.source = source
        self.row_number = row_number
        super().__init__(self._message())

    def _message(self):
        return "%s: %s" % (self.field, self.reason)

    def as_record(self):
        return {"source": self.source, "row": self.row_number,
                "field": self.field, "reason": self.reason}


class InputFileError(OSError):
    """Raised when an input file cannot be read safely."""