import sys
from openbabel import pybel

for mol in pybel.readfile("sdf", sys.argv[1]):
       mol.write("sdf", "%s.sdf" % mol.title,overwrite=True)
