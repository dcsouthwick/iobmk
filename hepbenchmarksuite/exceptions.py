###############################################################################
# Copyright 2019-2020 CERN. See the COPYRIGHT file at the top-level directory
# of this distribution. For licensing information, see the COPYING file at
# the top-level directory of this distribution.
###############################################################################


class PreFlightError(Exception):
    """Couldn't pass pre-flight checks."""
    pass

class BenchmarkFailure(Exception):
    """An exception for a failed benchmark."""
    pass

class BenchmarkFullFailure(Exception):
    """An exception for when all benchmarks failed."""
    pass
