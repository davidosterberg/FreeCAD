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

__title__ = "FreeCAD FEM solver Code Aster tasks"
__author__ = "Tim Swait"
__url__ = "https://www.freecad.org"

## \addtogroup FEM
#  @{

import os
import subprocess

import FreeCAD
import ObjectsFem

from . import writer
from .. import run
from .. import settings
from femmesh import meshsetsgetter
from femtools import femutils
from femtools import membertools
from feminout import importMedResults
from feminout import importToolsFem
from femresult import resulttools

_inputFileName = None


class Check(run.Check):

    def run(self):
        self.pushStatus("Checking analysis member...\n")
        self.check_mesh_exists()
        self.check_material_exists()
        #self.check_material_single()  # TODO: deal better with multiple materials
        self.check_geos_beamsection_single()  # no multiple beamsection
        self.check_geos_shellthickness_single()  # no multiple shellsection
        self.check_geos_beamsection_and_shellthickness()  # either beams or shells


class Prepare(run.Prepare):

    def run(self):
        global _inputFileName
        self.pushStatus("Preparing solver input...\n")

        # get mesh set data
        mesh_obj = membertools.get_mesh_to_solve(self.analysis)[0]  # pre check done already
        meshdatagetter = meshsetsgetter.MeshSetsGetter(
            self.analysis,
            self.solver,
            mesh_obj,
            membertools.AnalysisMember(self.analysis),
        )
        meshdatagetter.get_mesh_sets()

        # write solver input
        w = writer.FemInputWriterCodeAster(
            self.analysis,
            self.solver,
            mesh_obj,
            meshdatagetter.member,
            self.directory,
        )
        commpath, expath = w.write_solver_input()
        # report to user if task succeeded
        if expath != "":
            self.pushStatus(f"Writing solver input completed at {expath}\n")
        else:
            self.pushStatus("Writing solver input failed.\n")
            self.fail()
        _inputFileName = os.path.splitext(os.path.basename(expath))[0]


class Solve(run.Solve):

    def run(self):
        infile = _inputFileName + ".export"

        # get solver binary
        self.pushStatus("Get solver binary...\n")
        binary = settings.get_binary("CodeAster")
        if binary is None:
            self.fail()  # a print has been made in settings module
        # Delete previous result file:
        result_file = os.path.join(self.directory, _inputFileName + ".rmed")
        if os.path.isfile(result_file):
            self.pushStatus("Deleting old result file at {}\n".format(result_file))
            os.remove(result_file)

        # run solver
        self.pushStatus("Executing solver...\n")
        self._process = subprocess.Popen(
            args=[binary, infile],  # pass empty param fails! [binary, "", infile]
            cwd=self.directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.signalAbort.add(self._process.terminate)
        self._process.communicate()
        self.signalAbort.remove(self._process.terminate)

class Results(run.Results):

    def run(self):
        prefs = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/General")
        if not prefs.GetBool("KeepResultsOnReRun", False):
            self.purge_results()
        self.load_results()

    def purge_results(self):
        self.pushStatus("Purge existing results...\n")
        for m in membertools.get_member(self.analysis, "Fem::FemResultObject"):
            if femutils.is_of_type(m.Mesh, "Fem::MeshResult"):
                self.analysis.Document.removeObject(m.Mesh.Name)
            self.analysis.Document.removeObject(m.Name)
        #self.analysis.Document.recompute()

    def load_results(self):
        self.pushStatus("Import new results...\n")
        result_file = os.path.join(self.directory, _inputFileName + ".rmed")
        if os.path.isfile(result_file):
            mesh = importMedResults.read_med_mesh(result_file)
            result_set = importMedResults.read_med_result(result_file)
            results_name = 'CodeAsterResults'
            res_obj = ObjectsFem.makeResultMechanical(self.analysis.Document, results_name)
            result_mesh_object = ObjectsFem.makeMeshResult(self.analysis.Document, results_name + "_Mesh")
            result_mesh_object.FemMesh = mesh
            res_obj.Mesh = result_mesh_object
            res_obj = importToolsFem.fill_femresult_mechanical(res_obj, result_set)
            res_obj = resulttools.fill_femresult_stats(res_obj)
            self.analysis.addObject(res_obj)
        else:
            FreeCAD.Console.PrintError(f"FEM: No results found at {result_file}!\n")
            self.fail()


##  @}
