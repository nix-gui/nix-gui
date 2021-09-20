def Union:
    def __init__(self, *subtypes):
        self.subtypes = sorted(set(subtypes, key=str))
