"""
Correction de compatibilité Python 3.14 — appliquée automatiquement au démarrage.

Python 3.14 a changé le comportement des objets super() : ils n'acceptent plus
l'assignation d'attributs via __dict__. Django 5.0.6 utilisait copy(super())
dans BaseContext.__copy__, ce qui plante sur Python 3.14.
"""
import sys

if sys.version_info >= (3, 14):
    from django.template.context import BaseContext

    def _fixed_copy(self):
        cls = self.__class__
        duplicate = cls.__new__(cls)
        duplicate.__dict__.update(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate

    BaseContext.__copy__ = _fixed_copy
