"""Provide support for mapping configuration tags to classes."""
from typing import Type
from hyperconf.config import HyperConfig
from hyperconf.errors import DuplicateMappingError


def hypermap(tag: str):
    """Class decorator for defining tag-class maps.
    """
    if tag is None:
        raise ValueError("tag is None")
    
    def _decorator(cls: Type):
        HyperMap.register(tag, cls)
    return _decorator


class HyperMap:
    """Maintain a class registry.

    This class provides support for mapping Python classes to
    HyperConf configuration tags. Classes can be added either
    by using register_class or by using the hyperconf class
    decorator.
    """

    _tag2class = {}
    _class2tag = {}

    @staticmethod
    def register(tag: str, cls: Type):
        """Define a tag to class mapping.

        :param tag: the configuration tag.
        :param cls: a class object.
        """
        if tag is None:
            raise ValueError("tag is None")
        if cls is None:
            raise ValueError("cls is None")

        if tag in HyperMap._tag2class:
            raise DuplicateMappingError(
                tag, HyperMap._tag2class
            )
            
        HyperMap._tag2class[tag] = cls
        if cls not in HyperMap._class2tag:
            HyperMap._class2tag[cls] = [tag]
        else:
            HyperMap._class2tag[cls].append(tag)

    @staticmethod
    def get_class(tag: str):
        """Get the class associated with a configuration object tag.

        :param tag: the configuration object tag.
        :return: a class or None if no mapping is defined for the tag.
        """
        if tag is None:
            raise ValueError("tag is None")
        if not isinstance(tag, str):
            if isinstance(tag, HyperConfig):
                tag = tag.__def__.name
            else:
                # not a str or a hyperconf object
                raise ValueError("tag must be str or HyperConfig instance")
            
        if tag not in HyperMap._tag2class:
            return None
        return HyperMap._tag2class[tag]
