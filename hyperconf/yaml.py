"""Configuration template parsering utilities."""
from yaml.loader import SafeLoader


class LineInfoLoader(SafeLoader):
    """Adds line numbers to parsed yaml dicts."""

    def construct_mapping(self, node, deep=False):
        """Augument parsed nodes."""
        mapping = super().construct_mapping(node, deep=deep)
        mapping['__line__'] = node.start_mark.line + 1
        return mapping
