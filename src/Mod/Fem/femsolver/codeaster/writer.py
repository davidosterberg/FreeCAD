# ***************************************************************************
# *   Copyright (c) 2024 Tim Swait <timswait@gmail.com>                     *
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

__title__ = "Code Aster Writer"
__author__ = "Tim Swait"
__url__ = "https://www.freecad.org"

## \addtogroup FEM
#  @{

import time
from os.path import join

import FreeCAD

from . import add_mesh
from . import add_femelement_material
from . import add_femelement_geometry
from . import add_con_force
from . import add_con_fixed
from .. import writerbase
from femmesh import gmshtools
from .equations import elasticity_writer


class FemInputWriterCodeAster(writerbase.FemInputWriter):
    def __init__(
        self, analysis_obj, solver_obj, mesh_obj, member, dir_name=None, mat_geo_sets=None
    ):
        writerbase.FemInputWriter.__init__(
            self, analysis_obj, solver_obj, mesh_obj, member, dir_name, mat_geo_sets
        )

        if self.mesh_object is not None:
            self.basename = self.mesh_object.Name
        else:
            self.basename = "Mesh"
        if self.mesh_object.GroupsOfNodes:
            FreeCAD.Console.PrintWarning('Groups of Nodes must be set to False in {} for CA writer to be able to set groups. Changing this setting...\n'.format(self.mesh_object.Name))
            self.mesh_object.GroupsOfNodes = False
        self.tools = gmshtools.GmshTools(self.mesh_object)
        self.solverinput_file = join(self.dir_name, self.basename + ".comm")
        self.export_file = join(self.dir_name, self.basename + ".export")
        self.geo_file = join(self.dir_name, self.basename + ".geo")
        self.IPmesh_file = join(self.dir_name, self.basename + ".med")
        self.OPmesh_file = join(self.dir_name, self.basename + ".rmed")
        self.fixes = []
        self.forces = []
        FreeCAD.Console.PrintLog(f"FemInputWriterCodeAster --> self.dir_name  -->  {self.dir_name}\n")
        FreeCAD.Console.PrintMessage(
            "FemInputWriterCodeAster --> self.solverinput_file  -->  {}\n".format(self.solverinput_file)
        )
        FreeCAD.Console.PrintMessage(
            "FemInputWriterCodeAster --> self.export_file  -->  {}\n".format(self.export_file)
        )

    def write_solver_input(self):

        timestart = time.process_time()
        # only use the first material object TODO deal better with multi materials
        self.mat_objs = [ML["Object"] for ML in self.member.mats_linear]
        commtxt = "# Code Aster input comm file written from FreeCAD\n"
        commtxt += "DEBUT(LANG='EN')\n\n"
        commtxt = add_mesh.add_mesh(commtxt, self)
        commtxt = elasticity_writer.assign_elasticity_model(commtxt, self)
        commtxt = add_femelement_material.define_femelement_material(commtxt,self)
        commtxt, matnames = add_femelement_geometry.add_femelement_geometry(commtxt, self)
        commtxt = add_femelement_material.assign_femelement_material(commtxt,matnames, self)
        commtxt = add_con_fixed.add_con_fixed(commtxt, self)
        commtxt = add_con_force.add_con_force(commtxt, self)
        commtxt += "reslin = MECA_STATIQUE(CARA_ELEM=elemprop,\n"
        commtxt += "                       CHAM_MATER=fieldmat,\n"
        commtxt += "                       EXCIT=(_F(CHARGE={}),\n".format(self.fixes[0])
        commtxt += "                              _F(CHARGE={})),\n".format(self.forces[0])
        commtxt += "                       MODELE=model,\n"
        commtxt += "                       SOLVEUR=_F(RESI_RELA = {}))\n\n".format(self.solver_obj.SolverPrecision)

        commtxt += "IMPR_RESU(RESU=_F(CARA_ELEM=elemprop,\n"
        commtxt += "                  INFO_MAILLAGE='OUI',\n"
        commtxt += "                  MAILLAGE=mesh,\n"
        commtxt += "                  RESULTAT=reslin),\n"
        commtxt += "          UNITE=80)\n\n"
        commtxt += "FIN()\n"

        commfile = open(self.solverinput_file, 'w')
        commfile.write(commtxt)
        commfile.close()

        # Write updated .geo file into Gmsh folder and write .med file into SolverCodeAster folder
        self.tools.write_part_file()
        self.tools.write_geo()
        self.tools.get_gmsh_command()
        self.tools.run_gmsh_with_geo()

        exfile = open(self.export_file, 'w')
        exfile.write("# Code Aster export file written from FreeCAD\n")
        exfile.write("P actions make_etude\n")
        exfile.write("P lang en\n")
        exfile.write("P version stable\n")
        exfile.write("A args \n")
        exfile.write("A memjeveux 2000.0\n")
        exfile.write("A tpmax 900.0\n")
        exfile.write("F comm {} D  1\n".format(self.solverinput_file))
        exfile.write("F mmed {} D  20\n".format(self.IPmesh_file))
        exfile.write("F rmed {} R  80\n".format(self.OPmesh_file))
        exfile.write("F mess ./message R  6\n")
        exfile.close()

        writing_time_string = "Writing time input file: {} seconds".format(
            round((time.process_time() - timestart), 2)
        )
        FreeCAD.Console.PrintMessage(writing_time_string + " \n\n")

        return self.solverinput_file, self.export_file


##  @}
