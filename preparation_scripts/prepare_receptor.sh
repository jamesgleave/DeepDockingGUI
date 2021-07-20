receptor_f=$1
grid_points=$2 
grid_center=$3

if [ "$1" == "-h" ]; then
    echo "

PREPARE AUTODOCK DOCKING MAPS 

Usage: (ba)sh `basename $0` receptor grid_points grid_center path_adt

- receptor = receptor pdb file, prepared
- grid_points = 'x,y,z' format, point size of docking box (real size n_points*0.375 A)
- grid_center = 'x,y,z' format, coordinates of docking box center
- path_adt =  path to autodock tools folder with python scripts (prepare_receptor4.py, etc etc..)
"
    exit 0
fi

if [ "$1" != "-h" ] && [ $# -lt 4 ]; then
    echo "Not all the arguments were supplied; type 'sh prepare_receptor.sh -h' for help"
    exit 0
fi

receptor=$(echo $receptor_f|cut -d'.' -f1)

IFS=',' read -r -a dim<<<$grid_points
x_points="${dim[0]}"
y_points="${dim[1]}"
z_points="${dim[2]}"


IFS=',' read -r -a crd<<<$grid_center
x_crd="${crd[0]}"
y_crd="${crd[1]}"
z_crd="${crd[2]}"

python $4/prepare_receptor4.py -r $receptor_f -U nphs_lps_waters_nonstdres
wait

python $4/prepare_gpf4.py -r $receptor'.'pdbqt -o grid_1_$receptor'.'gpf -p ligand_types='P,SA,S,Cl,Ca,Mn,Fe,Zn,Br,I' -p npts=$grid_points -p gridcenter=$grid_center
wait

python $4/mnt/c/Program\ \Files\ \(x85\)/MGLTools-1.5.6/Lib/site-packages/AutoDockTools/Utilities24/prepare_gpf4.py -r $receptor'.'pdbqt -o grid_2_$receptor'.'gpf -p ligand_types='H,HD,HS,C,A,N,NA,NS,OA,OS,F,Mg' -p npts=$grid_points -p gridcenter=$grid_center
wait

autogrid4 -p grid_1_$receptor'.'gpf -l grid_1_$receptor'.'log
autogrid4 -p grid_2_$receptor'.'gpf -l grid_2_$receptor'.'log

rm *fld

echo "# AVS field file
#
# AutoDock Atomic Affinity and Electrostatic Grids
#
# Created by autogrid4.
#
#SPACING 0.375
#NELEMENTS $x_points $y_points $z_points 
#CENTER $x_crd $y_crd $z_crd
#MACROMOLECULE $receptor.pdbqt
#GRID_PARAMETER_FILE grid_$receptor.gpf
#
ndim=3			# number of dimensions in the field
dim1=$(($x_points+1))			# number of x-elements
dim2=$(($y_points+1))			# number of y-elements
dim3=$(($z_points+1))			# number of z-elements
nspace=3		# number of physical coordinates per point
veclen=24		# number of affinity values at each point
data=float		# data type (byte, integer, float, double)
field=uniform		# field type (uniform, rectilinear, irregular)
coord 1 file=$receptor.maps.xyz filetype=ascii offset=0
coord 2 file=$receptor.maps.xyz filetype=ascii offset=2
coord 3 file=$receptor.maps.xyz filetype=ascii offset=4
label=H-affinity	# component label for variable 1
label=HD-affinity	# component label for variable 2
label=HS-affinity	# component label for variable 3
label=C-affinity	# component label for variable 4
label=A-affinity	# component label for variable 5
label=N-affinity	# component label for variable 6
label=NA-affinity	# component label for variable 7
label=NS-affinity	# component label for variable 8
label=OA-affinity	# component label for variable 9
label=OS-affinity	# component label for variable 10
label=F-affinity        # component label for variable 11                                                    
label=Mg-affinity       # component label for variable 12                                                    
label=P-affinity        # component label for variable 13                                                    
label=SA-affinity       # component label for variable 14                                                    
label=S-affinity        # component label for variable 15                                                    
label=Cl-affinity       # component label for variable 16                                      
label=Ca-affinity       # component label for variable 17             
label=Mn-affinity       # component label for variable 18                                      
label=Fe-affinity       # component label for variable 19                                      
label=Zn-affinity       # component label for variable 20                                      
label=Br-affinity       # component label for variable 21                                      
label=I-affinity        # component label for variable 22                                      
label=Electrostatics    # component label for variable 22
label=Desolvation       # component label for variable 23 
#
# location of affinity grid files and how to read them
#
variable 1 file=$receptor.H.map filetype=ascii skip=6
variable 2 file=$receptor.HD.map filetype=ascii skip=6
variable 3 file=$receptor.HS.map filetype=ascii skip=6
variable 4 file=$receptor.C.map filetype=ascii skip=6
variable 5 file=$receptor.A.map filetype=ascii skip=6
variable 6 file=$receptor.N.map filetype=ascii skip=6
variable 7 file=$receptor.NA.map filetype=ascii skip=6
variable 8 file=$receptor.NS.map filetype=ascii skip=6
variable 9 file=$receptor.OA.map filetype=ascii skip=6
variable 10 file=$receptor.OS.map filetype=ascii skip=6
variable 11 file=$receptor.F.map filetype=ascii skip=6                                                                  
variable 12 file=$receptor.Mg.map filetype=ascii skip=6                                                                
variable 13 file=$receptor.P.map filetype=ascii skip=6                                                                  
variable 14 file=$receptor.SA.map filetype=ascii skip=6                                                                 
variable 15 file=$receptor.S.map filetype=ascii skip=6                                                                  
variable 16 file=$receptor.Cl.map filetype=ascii skip=6                                                                 
variable 17 file=$receptor.Ca.map filetype=ascii skip=6                                                                 
variable 18 file=$receptor.Mn.map filetype=ascii skip=6                                                                 
variable 19 file=$receptor.Fe.map filetype=ascii skip=6                                                                 
variable 20 file=$receptor.Zn.map filetype=ascii skip=6                                                                 
variable 21 file=$receptor.Br.map filetype=ascii skip=6                                                                 
variable 22 file=$receptor.I.map filetype=ascii skip=6                                                                  
variable 23 file=$receptor.e.map filetype=ascii skip=6                                                                  
variable 24 file=$receptor.d.map filetype=ascii skip=6">>$receptor.maps.fld

rm -r ad_grids
mkdir ad_grids
mv *map* ad_grids/
