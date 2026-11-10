"""Readonly observation seam; concrete native integration is initially unconfigured."""
class RetainedExit:
    def __init__(self, owned, key, role, *, api, clock):
        raise ValueError('Unconfigured retained native observation')
