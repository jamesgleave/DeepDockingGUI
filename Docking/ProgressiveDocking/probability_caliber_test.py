import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-n_it','--n_iteration',required=True)
parser.add_argument('-protein','--protein',required=True)
parser.add_argument('-file_path','--file_path',required=True)
#parser.add_argument('-mdd','--morgan_directory',required=True)

io_args = parser.parse_args()
n_iteration =  int(io_args.n_iteration)
protein = io_args.protein
file_path = io_args.file_path
#mdd=io_args.morgan_directory


import pandas as pd
import numpy as np
import glob
from tensorflow.keras.models import model_from_json


#protein_name = 'CAMKK2/mini_pd'
#file_path = '../'
#iteration_done = 1

    
def get_all_x_data(fname,y):
    train_set = np.zeros([1000000,1024])
    train_id = []
    with open(fname,'r') as ref:
        no=0
        for line in ref:
            tmp=line.rstrip().split(',')
            train_id.append(tmp[0])
            on_bit_vector = tmp[1:]
            for elem in on_bit_vector:
                train_set[no,int(elem)] = 1
            no+=1
        train_set = train_set[:no,:]
    train_pd = pd.DataFrame(data=train_set)
    train_pd['ZINC_ID'] = train_id
    if len(y.columns)!=2:
        y.reset_index(level=0,inplace=True)
    else:
        print('already 2 columns: ',fname)
    score_col = y.columns.difference(['ZINC_ID'])[0]
    train_data = pd.merge(y,train_pd,how='inner',on=['ZINC_ID'])
    X_train = train_data[train_data.columns.difference(['ZINC_ID',score_col])].values
    y_train = train_data[[score_col]].values
    return X_train,train_data.ZINC_ID,y_train


print('Loading vlaidation set')
try:
    valid_pd = pd.read_csv(file_path+'/'+protein+'/iteration_1/morgan/valid_morgan_1024_updated.csv',header=None,usecols=[0])
except:
    valid_pd = pd.read_csv(file_path+'/'+protein+'/iteration_1/morgan/valid_morgan_1024_updated.csv',header=None,usecols=[0],engine='python')
    try:
        if 'ZINC' in valid_pd.index[0]:
            valid_pd = pd.DataFrame(data=valid_pd.index)
    except:
        pass
valid_pd.columns= ['ZINC_ID']
valid_label = pd.read_csv(file_path+'/'+protein+'/iteration_1/validation_labels.txt',sep=',',header=0)
validation_data = pd.merge(valid_label,valid_pd,how='inner',on=['ZINC_ID'])
validation_data.set_index('ZINC_ID',inplace=True)
y_valid = validation_data

print('loading testing set')

try:
    test_pd = pd.read_csv(file_path+'/'+protein+'/iteration_1/morgan/test_morgan_1024_updated.csv',header=None,usecols=[0])
except:
    test_pd = pd.read_csv(file_path+'/'+protein+'/iteration_1/morgan/test_morgan_1024_updated.csv',header=None,usecols=[0],engine='python')
    try:
        if 'ZINC' in test_pd.index[0]:
            test_pd = pd.DataFrame(data=test_pd.index)
    except:
        pass
test_pd.columns= ['ZINC_ID']
test_label = pd.read_csv(file_path+'/'+protein+'/iteration_1/testing_labels.txt',sep=',',header=0)
testing_data = pd.merge(test_label,test_pd,how='inner',on=['ZINC_ID'])
testing_data.set_index('ZINC_ID',inplace=True)
y_test = testing_data

print('loading training set')

try:
    train_pd = pd.read_csv(file_path+'/'+protein+'/iteration_1/morgan/train_morgan_1024_updated.csv',header=None,usecols=[0])
except:
    train_pd = pd.read_csv(file_path+'/'+protein+'/iteration_1/morgan/train_morgan_1024_updated.csv',header=None,usecols=[0],engine='python')
    try:
        if 'ZINC' in train_pd.index[0]:
            train_pd = pd.DataFrame(data=train_pd.index)
    except:
        pass
train_pd.columns= ['ZINC_ID']
train_label = pd.read_csv(file_path+'/'+protein+'/iteration_1/training_labels.txt',sep=',',header=0)
training_data = pd.merge(train_label,train_pd,how='inner',on=['ZINC_ID'])
training_data.set_index('ZINC_ID',inplace=True)
y_train = training_data


X_valid,valid_zid,y_valid = get_all_x_data(file_path+'/'+protein+'/iteration_1/morgan/valid_morgan_1024_updated.csv',y_valid)

X_test,test_zid,y_test = get_all_x_data(file_path+'/'+protein+'/iteration_1/morgan/test_morgan_1024_updated.csv',y_test)

X_train,train_zid,y_train = get_all_x_data(file_path+'/'+protein+'/iteration_1/morgan/train_morgan_1024_updated.csv',y_train)

print('Done loading all')

if n_iteration==1:
    is_v2 = False
else:
    is_v2 = True

path_to_model = file_path+'/'+protein+'/iteration_'+str(n_iteration)+'/best_models/'
for f in glob.glob(path_to_model+'/*.json'):
    with open(f,'r') as ref:
        Progressive_docking = model_from_json(ref.read())
for f in glob.glob(path_to_model+'/*.h5'):
    Progressive_docking.load_weights(f)

if is_v2:
    print('using train as validaition')
    prediction_valid = Progressive_docking.predict(X_train)
else:
    print('using valid as validation')
    prediction_valid = Progressive_docking.predict(X_valid)
prediction_test = Progressive_docking.predict(X_test)

with open(file_path+'/'+protein+'/iteration_'+str(n_iteration)+'/best_models/thresholds.txt','r') as ref:
    cf = ref.readline().strip().split(',')[-1]

if is_v2:
    with open(file_path+'/'+protein+'/iteration_'+str(n_iteration)+'/calibration_set_cf_'+str(cf)+'.txt','w') as ref:
        ref.write('ZINC_ID,prediction_probability,docking_score\n')
        for i in range(len(prediction_valid)):
            ref.write(train_zid[i]+','+str(prediction_valid[i][0])+','+str(y_train[i][0])+'\n')
else:
    with open(file_path+'/'+protein+'/iteration_'+str(n_iteration)+'/calibration_set_cf_'+str(cf)+'.txt','w') as ref:
        ref.write('ZINC_ID,prediction_probability,docking_score\n')
        for i in range(len(prediction_valid)):
            ref.write(valid_zid[i]+','+str(prediction_valid[i][0])+','+str(y_valid[i][0])+'\n')

with open(file_path+'/'+protein+'/iteration_'+str(n_iteration)+'/testing_set_cf_'+str(cf)+'.txt','w') as ref:
        ref.write('ZINC_ID,prediction_probability,docking_score\n')
        for i in range(len(prediction_test)):
            ref.write(test_zid[i]+','+str(prediction_test[i][0])+','+str(y_test[i][0])+'\n')
