import sys
import os

ROOT = os.path.abspath(os.path.dirname(__file__))
APP = os.path.join(ROOT, "app")

# Ajouter la racine ET app/ au path pour que les imports absolus fonctionnent
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
if APP not in sys.path:
    sys.path.insert(0, APP)
