# ***************************************************************************
# *   Copyright (c) 2021 Bernd Hahnebach <bernd@bimstatik.org>              *
# *                                                                         *
# *   This file is part of the FreeCAD CAx development system.              *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************

__title__ = "FreeCAD FEM solver object Code Aster"
__author__ = "Tim Swait"
__url__ = "https://www.freecad.org"

## @package SolverCodeAster
#  \ingroup FEM

import glob
import os

import FreeCAD

from . import tasks
from .equations import elasticity
from .. import run
from .. import solverbase
from femtools import femutils

if FreeCAD.GuiUp:
    import FemGui

ANALYSIS_TYPES = ["static"]


def create(doc, name="SolverCodeAster"):
    return femutils.createObject(doc, name, Proxy, ViewProxy)


class Proxy(solverbase.Proxy):
    """The Fem::FemSolver's Proxy python type, add solver specific properties"""

    Type = "Fem::SolverCodeAster"

    _EQUATIONS = {
        "Elasticity": elasticity,
    }

    def __init__(self, obj):
        super().__init__(obj)
        obj.Proxy = self

        obj.addProperty("App::PropertyEnumeration", "AnalysisType", "Fem", "Type of the analysis")
        obj.AnalysisType = ANALYSIS_TYPES
        obj.AnalysisType = ANALYSIS_TYPES[0]
        obj.addProperty(
            "App::PropertyPrecision",
            "SolverPrecision",
            "Fem",
            "Precision of solver (a smaller number will quite with an error if this accuracy can't be met)",
        )
        obj.SolverPrecision = 1e-6

    def createMachine(self, obj, directory, testmode=False):
        return run.Machine(
            solver=obj,
            directory=directory,
            check=tasks.Check(),
            prepare=tasks.Prepare(),
            solve=tasks.Solve(),
            results=tasks.Results(),
            testmode=testmode,
        )

    def createEquation(self, doc, eqId):
        print("CREATING EQN")
        return self._EQUATIONS[eqId].create(doc)

    def isSupported(self, eqId):
        return eqId in self._EQUATIONS

    def editSupported(self):
        return True

    def edit(self, directory):
        pattern = os.path.join(directory, "*.export")
        FreeCAD.Console.PrintMessage(f"{pattern}\n")
        f = glob.glob(pattern)[0]
        FemGui.open(f)
        # see comment in oofem solver file

    def execute(self, obj):
        return


class ViewProxy(solverbase.ViewProxy):

    def getIcon(self):
        return ":/icons/FEM_SolverCodeAster.svg"


##  @}
