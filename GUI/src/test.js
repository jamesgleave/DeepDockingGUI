// Create a simple CO2 molecule
var mol = new Kekule.Molecule();
var atomC = mol.appendAtom('C');
var atomO1 = mol.appendAtom('O');
var atomO2 = mol.appendAtom('O');
mol.appendBond([atomC, atomO1], 2);
mol.appendBond([atomC, atomO2], 2);

// Get formula
var formula = mol.calcFormula();
console.log('Formula: ', formula.getText());

// Output SMILES (IO module should be loaded in web application)
var smiles = Kekule.IO.saveFormatData(mol, 'smi');
console.log('SMILES: ', smiles);

// Output MOL2k (IO module should be loaded in web application)
var mol2k = Kekule.IO.saveFormatData(mol, 'mol');
console.log('MOL 2000: \n', mol2k);
        