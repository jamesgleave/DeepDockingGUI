import pandas as pd
import time
import numpy as np
from tensorflow.keras.layers import Input,Dense,Activation, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.callbacks import EarlyStopping
import tensorflow as tf
#import keras_metrics
import argparse
from sklearn.metrics import auc
from sklearn.metrics import precision_recall_curve,roc_curve
from tensorflow.keras.layers.normalization import BatchNormalization
import random
import glob
import os,sys
# import keras_metrics
import argparse
import glob
import os
import random
import sys
import time

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import Input, Dense, Activation, Dropout
from tensorflow.keras.layers.normalization import BatchNormalization
from tensorflow.keras.models import Model
from sklearn.metrics import auc
from sklearn.metrics import precision_recall_curve, roc_curve

parser = argparse.ArgumentParser()
parser.add_argument('-file_n','--file_n',required=True)
io_args = parser.parse_args()
file_n = int(io_args.file_n)


def get_x_data(Oversampled_zid,fname):
    #train_set = np.zeros([1000000,1024])
    #train_id = []
    with open(fname,'r') as ref:
        no=0
        for line in ref:
            tmp=line.rstrip().split(',')
            if tmp[0] in Oversampled_zid.keys():
                if type(Oversampled_zid[tmp[0]])!=np.ndarray:
                    train_set = np.zeros([1,1024])
                    on_bit_vector = tmp[1:]
                    for elem in on_bit_vector:
                        train_set[0,int(elem)] = 1
                    Oversampled_zid[tmp[0]] = np.repeat(train_set,Oversampled_zid[tmp[0]],axis=0)
                    
def get_all_x_data(fname,y):
    train_set = np.zeros([3000000,1024])
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
    #y['ZINC_ID'] = y.index
    train_data = pd.merge(y,train_pd,how='inner',on=['ZINC_ID'])
    X_train = train_data[train_data.columns.difference(['ZINC_ID',score_col])].values
    y_train = train_data[[score_col]].values
    return X_train,y_train

location = '/groups/cherkasvgrp/share/progressive_docking/pd_1_billion_oed/pd_1_billion_current/'
file_path = location
all_proteins = []
for f in glob.glob(location+'/????'):
    all_proteins.append(f)
    
print(all_proteins)

all_protein_hyperpara = []

for f in all_proteins:
    try:
        temp = []
        temp.append([10, 256, 0.0001, 3, 1500, 0.7, 2.0, 1, 1300])
        all_protein_hyperpara.append([f,*temp])
    except:
        print(f)
        
sampling_sizes = [10000,20000,40000,80000,160000,320000,640000,985000]

all_protein_hyperpara = [all_protein_hyperpara[file_n]]  

for file_name,hyp in all_protein_hyperpara:
    protein = file_name.split('/')[-1]
    if os.path.isfile(file_path+'/'+protein+'/iteration_'+str(1)+'/sampling_5_times.csv'):
        if len(pd.read_csv(file_path+'/'+protein+'/iteration_'+str(1)+'/sampling_5_times.csv',header=None))==len(sampling_sizes)*5:
            print('skipping: '+protein)
            continue
        else:
            print('removing: ',protein)
            #print(file_path+'/'+protein+'/iteration_'+str(1)+'/sampling_5_times.csv')
            os.remove(file_path+'/'+protein+'/iteration_'+str(1)+'/sampling_5_times.csv')
    for samp_sz in sampling_sizes:
        for n_run in range(5):
            #protein = file_name.split('/')[-1]
            print(file_name,samp_sz,n_run+1)
            oss,bs,lr,ba,nu,df,wt,n_it,t_mol = hyp
            prefix = ['_morgan_1024_updated.csv']
            prefix_label = ['']
            n_iteration = n_it
            total_mols = t_mol
            is_v2 = False
            try:
                train_pd = pd.read_csv(file_path+'/'+protein+'/iteration_'+str(n_iteration)+'/morgan/train'+prefix[0],header=None,usecols=[0])
            except:
                train_pd = pd.read_csv(file_path+'/'+protein+'/iteration_'+str(n_iteration)+'/morgan/train'+prefix[0],header=None,usecols=[0],engine='python')
                try:
                    if 'ZINC' in train_pd.index[0]:
                        train_pd = pd.DataFrame(data=train_pd.index)
                except:
                    pass
            train_pd.columns= ['ZINC_ID']
            try:
                valid_pd = pd.read_csv(file_path+'/'+protein+'/iteration_'+str(n_iteration)+'/morgan/valid'+prefix[0],header=None,usecols=[0])
            except:
                valid_pd = pd.read_csv(file_path+'/'+protein+'/iteration_'+str(n_iteration)+'/morgan/valid'+prefix[0],header=None,usecols=[0],engine='python')
                try:
                    if 'ZINC' in valid_pd.index[0]:
                        valid_pd = pd.DataFrame(data=valid_pd.index)
                except:
                    pass
            valid_pd.columns= ['ZINC_ID']
            try:
                test_pd = pd.read_csv(file_path+'/'+protein+'/iteration_'+str(n_iteration)+'/morgan/test'+prefix[0],header=None,usecols=[0])
            except:
                test_pd = pd.read_csv(file_path+'/'+protein+'/iteration_'+str(n_iteration)+'/morgan/test'+prefix[0],header=None,usecols=[0],engine='python')
                try:
                    if 'ZINC' in test_pd.index[0]:
                        test_pd = pd.DataFrame(data=test_pd.index)
                except:
                    pass
            test_pd.columns= ['ZINC_ID']
            train_label = pd.read_csv(file_path+'/'+protein+'/iteration_'+str(n_iteration)+'/training_labels'+prefix_label[0]+'.txt',sep=',',header=0)
            valid_label = pd.read_csv(file_path+'/'+protein+'/iteration_'+str(n_iteration)+'/validation_labels'+prefix_label[0]+'.txt',sep=',',header=0)
            test_label = pd.read_csv(file_path+'/'+protein+'/iteration_'+str(n_iteration)+'/testing_labels'+prefix_label[0]+'.txt',sep=',',header=0)
            train_label.columns=['r_i_docking_score','ZINC_ID']
            valid_label.columns=['r_i_docking_score','ZINC_ID']
            test_label.columns=['r_i_docking_score','ZINC_ID']
            print(train_label.head(1))
            print(valid_label.head(1))
            print(test_label.head(1))
            print(train_pd.head(1))
            print(valid_pd.head(1))
            print(test_pd.head(1))
            train_data = pd.merge(train_label,train_pd,how='inner',on=['ZINC_ID'])
            validation_data = pd.merge(valid_label,valid_pd,how='inner',on=['ZINC_ID'])
            train_data.set_index('ZINC_ID',inplace=True)
            validation_data.set_index('ZINC_ID',inplace=True)
            test_data = pd.merge(test_label,test_pd,how='inner',on=['ZINC_ID'])
            test_data.set_index('ZINC_ID',inplace=True)

            train_pd = []
            valid_pd = []
            test_pd = []
            train_label = []
            valid_label = []
            test_label = []

            print(train_data.shape,validation_data.shape,test_data.shape)
            
            good_mol = int(100*t_mol/13)
            
            scores_val = validation_data.values
            cf_start = np.mean(scores_val)
            print(cf_start,good_mol)
            while 1==1:
                t_good = len(scores_val[scores_val<cf_start])
                if t_good<=good_mol:
                    break
                cf_start = cf_start - 0.005
            
            cf = cf_start
            print(cf)
            
            y_train = train_data<cf
            y_valid = validation_data<cf
            y_test = test_data<cf

            train_data = []
            validation_data = []
            test_data = []

            if n_iteration==1:
                y_train = y_train
                y_valid = y_valid
                y_test = y_test
            else:
                y_train = pd.concat([y_train,y_test,y_valid],axis=0)
                y_valid = y_valid_fn
                y_test = y_test_fn

            t_train_mol = len(y_train)
            pos_ct_orig = y_train.r_i_docking_score.sum()

            print(y_train.shape)

            if y_valid.sum().values<=10:
                sys.exit()

            if y_test.sum().values<=10:
                sys.exit()

            try:
                y_train = pd.concat([y_train,y_old_full])
            except:
                pass

            y_train = y_train.sample(np.min([samp_sz,len(y_train)]))
            y_valid = y_valid.sample(np.min([samp_sz,1000000]))
            y_test = y_test.sample(np.min([samp_sz,1000000]))

            print(y_train.shape)

            y_pos = y_train[y_train.r_i_docking_score==1]
            y_neg = y_train[y_train.r_i_docking_score==0]


            neg_ct = y_neg.shape[0]
            pos_ct = y_pos.shape[0]
            
            print(pos_ct,pos_ct_orig,neg_ct)

            #sample_size = np.min([neg_ct,pos_ct*oss])

            sample_size = np.min([neg_ct,500000,pos_ct*oss])

            print(sample_size)

            Oversampled_zid = {}
            Oversampled_zid_y = {}
            for i in range(sample_size):
                idx = random.randint(0,pos_ct-1)
                idx_neg = random.randint(0,neg_ct-1)
                try:
                    Oversampled_zid[y_pos.index[idx]] +=1
                except:
                    Oversampled_zid[y_pos.index[idx]] = 1
                    Oversampled_zid_y[y_pos.index[idx]] = 1
                try:
                    Oversampled_zid[y_neg.index[idx_neg]] +=1
                except:
                    Oversampled_zid[y_neg.index[idx_neg]] = 1
                    Oversampled_zid_y[y_neg.index[idx_neg]] = 0
            y_pos = []
            y_neg = []

            #y_valid_temp = y_valid
            print(y_valid.shape)
            for i in range(n_iteration):
                for f in glob.glob(file_path+'/'+protein+'/iteration_'+str(i+1)+'/morgan/*'):
                    if i==0:
                        if f.split('/')[-1].split('_')[0]=='valid':
                            X_valid,y_valid = get_all_x_data(f,y_valid)
                        elif f.split('/')[-1].split('_')[0]=='test':
                            X_test,y_test = get_all_x_data(f,y_test)
                        else:
                            if is_v2:
                                print('Its V2')
                                X_test_2,y_test_2 = get_all_x_data(f,y_test_fn_2) 
                            else:
                                get_x_data(Oversampled_zid,f)
                    else:
                        get_x_data(Oversampled_zid,f)

            #if is_v2:
            #    print(X_valid.shape,X_valid_2.shape)
            #    X_valid = np.concatenate([X_valid,X_valid_2])
            #    y_valid = np.concatenate([y_valid,y_valid_2])
            #    print(y_valid.shape)

            #y_valid_temp = []
            #X_valid_2 = []
            #y_valid_2 = []

            ct= 0 
            Oversampled_X_train = np.zeros([sample_size*2,1024])
            Oversampled_y_train = np.zeros([sample_size*2,1])
            for keys in Oversampled_zid.keys():
                tt = len(Oversampled_zid[keys])
                Oversampled_X_train[ct:ct+tt] = Oversampled_zid[keys]
                Oversampled_y_train[ct:ct+tt] = Oversampled_zid_y[keys]
                ct +=tt

            try:
                print(Oversampled_X_train.shape,Oversampled_y_train.shape,X_valid.shape,y_valid.shape,X_test.shape,y_test.shape)
            except:
                print(Oversampled_X_train.shape,Oversampled_y_train.shape,X_valid.shape,y_valid.shape)


            from tensorflow.keras.callbacks import Callback
            class TimedStopping(Callback):
                '''Stop training when enough time has passed.
                # Arguments
                    seconds: maximum time before stopping.
                    verbose: verbosity mode.
                '''
                def __init__(self, seconds=None, verbose=1):
                    super(Callback, self).__init__()

                    self.start_time = 0
                    self.seconds = seconds
                    self.verbose = verbose

                def on_train_begin(self, logs={}):
                    self.start_time = time.time()

                def on_epoch_end(self, epoch, logs={}):
                    print('epoch done')
                    if time.time() - self.start_time > self.seconds:
                        self.model.stop_training = True
                        if self.verbose:
                            print('Stopping after %s seconds.' % self.seconds)


            def Progressive_Docking(input_shape,num_units=32,bin_array=[0,1,0],dropoutfreq=0.8):
                X_input = Input(input_shape)
                X = X_input
                for j,i in enumerate(bin_array):
                    if i==0:
                        X = Dense(num_units,name="Hidden_Layer_%i"%(j+1))(X)
                        X = BatchNormalization()(X)
                        X = Activation('relu')(X)
                    else:
                        X = Dropout(dropoutfreq)(X)
                X = Dense(1,activation='sigmoid',name="Output_Layer")(X)
                model = Model(inputs = X_input,outputs=X,name='Progressive_Docking')
                return model

            progressive_docking = Progressive_Docking(Oversampled_X_train.shape[1:],num_units=nu,bin_array=ba*[0,1],dropoutfreq=df)

            adam_opt = tf.train.AdamOptimizer(learning_rate=lr,epsilon=1e-06)
            progressive_docking.compile(optimizer=adam_opt,loss='binary_crossentropy',metrics=['accuracy'])

            es = EarlyStopping(monitor='val_loss',min_delta=0,patience=10,verbose=0,mode='auto')
            es1 = TimedStopping(seconds=10800)
            cw = {0:wt,1:1}

            progressive_docking.fit(Oversampled_X_train,Oversampled_y_train,epochs=500,batch_size=bs,shuffle=True,class_weight=cw,verbose=1,validation_data=[X_valid,y_valid],callbacks=[es,es1])

            #prediction_train = progressive_docking.predict(X_train)
            if is_v2:
                print('using train as validation')
                prediction_valid = progressive_docking.predict(X_test_2)
                precision_vl, recall_vl, thresholds_vl = precision_recall_curve(y_test_2,prediction_valid)
                fpr_vl, tpr_vl, thresh_vl = roc_curve(y_test_2, prediction_valid)
                auc_vl = auc(fpr_vl,tpr_vl)
                pr_vl = precision_vl[np.where(recall_vl>0.9)[0][-1]]
                pos_ct_orig = np.sum(y_test_2)
                Total_left = 0.9*total_mols/pr_vl*pos_ct_orig/len(y_test_2)*1000000
                tr = thresholds_vl[np.where(recall_vl>0.90)[0][-1]]
            else:
                print('using valid as validation')
                prediction_valid = progressive_docking.predict(X_valid)
                precision_vl, recall_vl, thresholds_vl = precision_recall_curve(y_valid,prediction_valid)
                fpr_vl, tpr_vl, thresh_vl = roc_curve(y_valid, prediction_valid)
                auc_vl = auc(fpr_vl,tpr_vl)
                pr_vl = precision_vl[np.where(recall_vl>0.9)[0][-1]]
                pos_ct_orig = np.sum(y_valid)
                Total_left = 0.9*pos_ct_orig/pr_vl*total_mols*1000000/len(y_valid)
                tr = thresholds_vl[np.where(recall_vl>0.90)[0][-1]]
                
            prediction_test = progressive_docking.predict(X_test)
            precision_te, recall_te, thresholds_te = precision_recall_curve(y_test,prediction_test)
            fpr_te, tpr_te, thresh_te = roc_curve(y_test, prediction_test)
            auc_te = auc(fpr_te,tpr_te)
            pr_te = precision_te[np.where(thresholds_te>tr)[0][0]]
            re_te = recall_te[np.where(thresholds_te>tr)[0][0]]
            pos_ct_orig = np.sum(y_test)
            Total_left_te = re_te*pos_ct_orig/pr_te*total_mols*1000000/len(y_test)
            
            random_precision = np.sum(y_valid)/len(y_valid)
            
            with open(file_path+'/'+protein+'/iteration_'+str(n_iteration)+'/sampling_5_times.csv','a') as ref:
                ref.write(str(samp_sz)+','+str(oss)+','+str(bs)+','+str(lr)+','+str(ba)+','+str(nu)+','+str(df)+','+str(wt)+','+str(cf)+','+str(auc_vl)+','+str(pr_vl)+','+str(Total_left)+','+str(auc_te)+','+str(pr_te)+','+str(re_te)+','+str(Total_left_te)+','+str(random_precision)+','+str(pr_te/random_precision)+','+str(pos_ct_orig)+'\n')
