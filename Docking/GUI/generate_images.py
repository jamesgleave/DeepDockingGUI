import os


def generate_model_image(model_path):
    model_name = os.path.basename(model_path)
    iteration = os.path.basename(model_path.replace("/all_models/" + model_name, ""))
    file_name = "GUI/images/models/{}_{}.png".format(model_name, iteration)

    # check if the image already exists... if it does then skip generating a new one
    if not os.path.exists(file_name):
        import tensorflow as tf
        from tensorflow.keras.models import load_model
        tf.keras.utils.plot_model(
            load_model(model_path),
            to_file=file_name,
            show_shapes=True,
            show_layer_names=True)

    # Grab the hyperparameter info
    from ML.Parser import Parser
    try:
        info = Parser.parse_ddss(model_path + ".ddss")
    except FileNotFoundError:
        info = {}
    print(file_name + "&&&" + str(info))


def generate_molecule_image(path, limit=25):
    from rdkit.Chem.Scaffolds import MurckoScaffold
    from rdkit.Chem import MolFromSmiles
    from rdkit.Chem.Draw import MolToImage
    from PIL import ImageDraw

    if os.path.exists(path):
        # Read the hits file
        smiles = []
        ids = []
        with open(path, 'r') as top_hits:
            for line_number, line in enumerate(top_hits.readlines()):
                if line_number >= limit:
                    break
                smiles.append(line.split(" ")[0])
                ids.append(line.split(" ")[1])

        # Generate scaffold
        for smile, mid in zip(smiles, ids):
            mol = MurckoScaffold.GetScaffoldForMol(MolFromSmiles(smile))
            image = MolToImage(mol)

            # Add text to the image
            draw = ImageDraw.Draw(image)
            draw.text((5, 5), mid, fill="black", align="right")
            image.save("GUI/images/molecules/{}.png".format(smile))
    else:
        return


if __name__ == '__main__':
    import argparse
    import sys
    sys.path.append(".")

    parser = argparse.ArgumentParser()
    parser.add_argument("--image_of", '-imof')
    parser.add_argument("--path_to_model")
    parser.add_argument("--path_to_molecules")
    args = parser.parse_args()

    try:
        os.mkdir("GUI/images")
        os.mkdir("GUI/images/molecules")
        os.mkdir("GUI/images/models")
    except OSError:
        pass

    if args.image_of == 'model':
        generate_model_image(args.path_to_model)
    elif args.image_of in {"molec", "molecule"}:
        generate_molecule_image(args.path_to_molecules)