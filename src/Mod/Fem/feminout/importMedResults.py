# ***************************************************************************
# *   Copyright (c) 2024 Tim Swait <timswait@gmail.com>                     *
# *   Copyright (c) 2024 Julian Todd <julian@goatchurch.org.uk >            *
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

__title__ = "Import of .med file containing mesh and results field data"
__author__ = "Tim Swait, Julian Todd"
__url__ = "https://www.freecad.org"

## @package importMedResults
#  \ingroup FEM
#  \brief FreeCAD med file results reader


import FreeCAD

# we need to import FreeCAD before the non FreeCAD library because of the print
try:
    import sys

    param_group = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Fem/CodeAster")
    mcPath = param_group.GetString("medcouplingPath")
    sys.path.append(mcPath)
    import medcoupling as mc
except Exception:
    FreeCAD.Console.PrintError("Module medcoupling not found. Cannot load med file.\n")

from . import importToolsFem

fname = "FEMMeshGmsh.rmed"


def read_med_mesh(medfile):
    """
    Function to read geometry of mesh from a .med file (So far only reads tria3 meshes)
    """

    FreeCAD.Console.PrintMessage(
        f"FEM: Results file found, reading codeaster results from: {medfile}\n"
    )
    m = mc.ReadMeshFromFile(medfile)
    nodes = {}
    for id in m.getNodeIdsInUse()[0]:
        nodes[id[0] + 1] = m.getCoordinatesOfNode(
            id[0]
        )  # NOTE: FreeCAD mesh node naming starts at 1, MED starts at 0.
    elements_tria3 = {}
    for e in range(m.getNumberOfCells()):
        assert m.getTypeOfCell(e) == 3, "Only tria3 elements supported at present"
        nids = m.getNodeIdsOfCell(e)
        elements_tria3[e + 1] = (nids[0] + 1, nids[1] + 1, nids[2] + 1)
    mesh = importToolsFem.make_femmesh(
        {
            "Nodes": nodes,
            "Seg2Elem": [],
            "Seg3Elem": [],
            "Tria3Elem": elements_tria3,
            "Tria6Elem": [],
            "Quad4Elem": [],
            "Quad8Elem": [],
            "Tetra4Elem": [],
            "Tetra10Elem": [],
            "Hexa8Elem": [],
            "Hexa20Elem": [],
            "Penta6Elem": [],
            "Penta15Elem": [],
        }
    )
    return mesh


def read_med_result(medfile):
    fieldname = mc.GetAllFieldNames(medfile)[0]
    q = mc.ReadField(medfile, fieldname).getArrays()[0]
    # columns = [q.getInfoOnComponent(i) for i in range(q.getNumberOfComponents())]
    disp = {}
    for i in range(q.getNumberOfTuples()):
        tup = q.getTuple(i)
        disp[i + 1] = FreeCAD.Vector(tup[0], tup[1], tup[2])
    result_set = {"disp": disp}
    return result_set


# m = read_aster_result(fname)
# mesh = feminout.importToolsFem.make_femmesh(m)

# res_obj = ObjectsFem.makeResultMechanical(doc, results_name)
# result_mesh_object = ObjectsFem.makeMeshResult(doc, results_name + "_Mesh")
# result_mesh_object.FemMesh = mesh
# res_obj.Mesh = result_mesh_object
