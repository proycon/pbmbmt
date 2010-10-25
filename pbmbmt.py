#!/usr/bin/env python
#-*- coding:utf-8 -*-

# PBMBMT: PHRASE-BASED MEMORY-BASED MACHINE TRANSLATOR: Meta script for running experiments
# by Maarten van Gompel (proycon)
#   proycon AT anaproy DOT NL
#   http://proylt.anaproy.nl
# Licensed under the GNU Public License v3


from pynlpl.evaluation import AbstractExperiment, ProcessFailed
from config import PBMBMTDIR, MATREXDIR, EXPDIR, TIMBL
import random
import os
import datetime
import sys
import glob
import shutil

class PBMBMTExperiment(AbstractExperiment):
    def __init__(self, data, **parameters):
        assert ((isinstance(data,tuple)) and (len(data) == 3))
        super(PBMBMTExperiment,self).__init__(data, **parameters)

    def run(self):
        if 'generation' in self.parameters:
            params = self.parameters['generation']
        else:
            params = {}
        PBMBMTInstanceGenerationExperiment( self.inputdata, **params ).run()
        if 'classifier' in self.parameters:
            params = self.parameters['classifier']
        else:
            params = {}
        PBMBMTClassifierExperiment( self.inputdata, **params).run()
        if 'decoder' in self.parameters:
            params = self.parameters['decoder']
        else:
            params = {}
        params['branch'] = False
        self.decodeexperiment = PBMBMTDecodeExperiment( self.inputdata,**params)
        self.decodeexperiment.run()



class PBMBMTAbstractInstanceGenerationExperiment(AbstractExperiment):
    def __init__(self, data, **parameters):
        """data: ( source, reference, set), for example: ('OpenSub-dutch', 'dev') """
        assert isinstance(data,tuple)
        if len(data) == 3:
            data = (data[0], data[-1]) #accept ('OpenSub-dutch', 'OpenSub-english','dev') input as well
        assert (len(data) == 2)
        super(PBMBMTAbstractInstanceGenerationExperiment,self).__init__(data, **parameters)

        #self.label = ''
        #for key in sorted(self.parameters.keys()):
        #    self.label += key.replace(['-','='],'') + str(self.parameters[key]).replace('0.','') #no hyphens or periods in label
        if not '-o' in parameters: #support for labels/infixes
            self.dir = EXPDIR + '/' + data[1]+ '/' + data[0]
        else:   
            self.dir = EXPDIR + '/' + data[1]+ '/' + data[0] + '.' + parameters['-o']

        try:
            os.mkdir(self.dir)
        except:
            pass

        if not '-l' in self.parameters and not '-L' in self.parameters and not '-m' in self.parameters and not '-M' in self.parameters and not '-p' in self.parameters:
            #use a phrasetable by default
            self.parameters['-p'] = EXPDIR + '/' + self.inputdata[0] + '.train.phrasetable'

    def defaultparameters(self):
        return {'--nfeatleft=':1, '--nfeatright=':1,'--nclassleft=':0,'--nclassright=':0}



class PBMBMTInstanceGenerationExperiment(PBMBMTAbstractInstanceGenerationExperiment):
    def __init__(self, data, **parameters):
        super(PBMBMTInstanceGenerationExperiment,self).__init__(data, **parameters)
        self.train = PBMBMTTrainGenExperiment(data, **parameters)
        self.test = PBMBMTTestGenExperiment(data, **parameters)

    def start(self):
        self.train.start()
        self.test.start()
    

    def done(self):
        self.train.process.poll() #TODO: verify poll doesn't raise an exception after process is already terminated and polled before?
        self.test.process.poll()
        return (self.train.process.returncode != None) and (self.test.process.returncode != None)

    

class PBMBMTTrainGenExperiment(PBMBMTAbstractInstanceGenerationExperiment):
    def __init__(self, data, **parameters):
        super(PBMBMTTrainGenExperiment,self).__init__(data, **parameters)


    def start(self):

        set = self.inputdata[1]

        #generate training instances
        stdout = open(self.dir + '/traininstancegen.out','w')
        stderr = open(self.dir + '/traininstancegen.err','w')

        print >>sys.stderr,"GENERATING TRAINING INSTANCES: ", repr(self.parameters)


        traingenparameters = {}
        for key, value in self.parameters.items(): #make copy
            traingenparameters[key] = value
        traingenparameters['--train='] =  self.inputdata[0] + '.train.A3.final'
        self.startcommand(PBMBMTDIR + '/pbmbmt-make-instances', EXPDIR + '/' + set, stdout, stderr, **traingenparameters)

    def done(self):
        try:
            return super(PBMBMTTrainGenExperiment, self).done()
        except ProcessFailed:
            print >>sys.stderr,"*** UNABLE TO GENERATE TRAINING INSTANCES! PROCESS EXITED WITH ERROR CODE! Check " + self.dir + "/traininstancegen.err ! ***"
            return True
        

class PBMBMTTestGenExperiment(PBMBMTAbstractInstanceGenerationExperiment):
    def __init__(self, data, **parameters):
        super(PBMBMTTestGenExperiment,self).__init__(data, **parameters)


    def start(self):

        set = self.inputdata[1]

        stdout = open(self.dir + '/testinstancegen.out','w')
        stderr = open(self.dir + '/testinstancegen.err','w')

        print >>sys.stderr,"GENERATING TEST INSTANCES: ", repr(self.parameters)

        #generate test instances
        testgenparameters = {}
        for key, value in self.parameters.items(): #make copy
            testgenparameters[key] = value
        testgenparameters['--test='] = self.inputdata[0] + '.' + set + '.txt'
        self.startcommand(PBMBMTDIR + '/pbmbmt-make-instances', EXPDIR + '/' + set, stdout, stderr, **testgenparameters)


    def done(self):
        try:
            return super(PBMBMTTestGenExperiment, self).done()
        except ProcessFailed:
            print >>sys.stderr,"*** UNABLE TO GENERATE TRAINING INSTANCES! PROCESS EXITED WITH ERROR CODE! Check " + self.dir + "/traininstancegen.err ! ***"
            return True
        


class PBMBMTClassifierExperiment(AbstractExperiment):
    def __init__(self, data, **parameters):
        """data: ( source, reference, set), for example: ('OpenSub-dutch', 'test') """
        assert isinstance(data,tuple)
        if len(data) == 3:
            data = (data[0], data[-1]) #accept ('OpenSub-dutch', 'OpenSub-english','dev') input as well
        assert (len(data) == 2)
        super(PBMBMTClassifierExperiment,self).__init__(data, **parameters)

        #self.label = ''
        #for key in sorted(self.parameters.keys()):
        #    self.label += key.replace(['-','='],'') + str(self.parameters[key]).replace('0.','') #no hyphens or periods in label

        if not 'infix' in parameters: #support for labels/infixes
            self.dir = EXPDIR + '/' + data[1]+ '/' + data[0]
        else:   
            self.dir = EXPDIR + '/' + data[1]+ '/' + data[0] + '.' + parameters['infix']

    def defaultparameters(self):
        return {'-k':1,'-a':4,'+v':'db','argdelimiter':'','+D':True} #(argdelimiter will be interpreted by startcommand(), not timbl)

    def start(self):
        self.processes = []
        print >>sys.stderr,"RUNNING CLASSIFIERS: ", repr(self.parameters)
        for trainfile in glob.glob(self.dir + '/*.train.*.inst'):
            filename = os.path.basename(trainfile)
            print >>sys.stderr,"\t" + filename

            multiconf = filename.split('.')[-3] #things like 111 , multi-classifier mode
            infix = ''
            if 'infix' in self.parameters:
                testfile = self.dir + '/' + self.inputdata[0] + '.' + self.parameters['infix'] + '.test.' + multiconf + '.inst'
            else:
                testfile = self.dir + '/' + self.inputdata[0] + '.test.' + multiconf + '.inst'



            if os.path.exists(testfile):
                params = {}
                for key, value in self.parameters.items(): #make copy
                    if key != 'infix':
                        params[key] = value
                params['-f'] = trainfile
                params['-t'] = testfile
                self.processes.append ( self.startcommand(TIMBL, self.dir, open(self.dir + '/timbl.out','w'), open(self.dir + '/timbl.err','w'), **params)  ) #TODO: different classifier overwrite same output file??
            else:
                print >>sys.stderr,"ERROR: Test instances do not exist in " + testfile


    def done(self):
        for p in self.processes:
            p.poll()
            if p.returncode == None:
                return False
            elif p.returncode > 0:
                print >>sys.stderr,"*** UNABLE TO CLASSIFY! TIMBL EXITED WITH ERROR CODE! Check " + self.dir + "/timbl.err ! ***"
                self.processes.remove(p)
        return True


class PBMBMTParamSearchClassifierExperiment(PBMBMTClassifierExperiment):
    def __init__(self,data):
        super(PBMBMTParamSearchClassifierExperiment,self).__init__(data, **parameters)

    def start(self):
        self.processes = []
        print >>sys.stderr,"RUNNING CLASSIFIERS: ", repr(self.parameters)
        for trainfile in glob.glob(self.dir + '/*.train.*.inst'):
            filename = os.path.basename(trainfile)
            print >>sys.stderr,"\t" + filename

            multiconf = filename.split('.')[-3] #things like 111 , multi-classifier mode
            infix = ''
            if 'infix' in self.parameters:
                testfile = self.dir + '/' + self.inputdata[0] + '.' + parameters['infix'] + '.test.' + multiconf + '.inst'
            else:
                testfile = self.dir + '/' + self.inputdata[0] + '.test.' + multiconf + '.inst'



            if os.path.exists(testfile):
                params = {}
                for key, value in self.parameters.items(): #make copy
                    if key != 'infix':
                        params[key] = value
                params['-f'] = trainfile
                params['-t'] = testfile
                self.processes.append ( self.startcommand(TIMBL, self.dir, open(self.dir + '/timbl.out','w'), open(self.dir + '/timbl.err','w'), **params)  )
            else:
                print >>sys.stderr,"ERROR: Test instances do not exist in " + testfile


class PBMBMTDecodeExperiment(AbstractExperiment):
    def __init__(self, data, **parameters):
        """data: ( source, reference, set), for example: ('OpenSub-dutch', 'OpenSub-english','dev') """
        global EXPDIR
        assert (isinstance(data,tuple) and (len(data) == 3))
        super(PBMBMTDecodeExperiment,self).__init__(data, **parameters)
        
        self.label = ''
        if 'branch' in self.parameters and self.parameters['branch']:
            if '-o' in parameters:
                self.infix = parameters['-o']
                self.label = parameters['-o'] + '_'


            for key in sorted(self.parameters.keys()):
                if key != 'branch' and key.find('=') == -1: #make nicer
                    self.label += key.replace('-','') + str(self.parameters[key]).replace('.',',') #no hyphens or periods in label
            self.label = self.label.replace('True','')
            self.dir = EXPDIR + '/' + data[2] + '/' + data[0] + '.' + self.label
        elif '-o' in parameters:
            self.infix = parameters['-o']
            self.dir = EXPDIR + '/' + data[2] + '/' + data[0] + '.' + self.infix
        else:
            self.dir = EXPDIR + '/' + data[2] + '/' + data[0]

        try:
            os.mkdir(self.dir)
        except:
            pass

    def defaultparameters(self):
        return {'-b':5,'-f':20,'-D':0.25, '-B':0.8, '-W': 1, 'branch':True}


    def start(self):

        if not os.path.isdir(self.dir):
            os.mkdir(self.dir)


        stdout = open(self.dir + '/decode.out','w')
        stderr = open(self.dir + '/decode.err','w')

        sourcedata, refdata,set = self.inputdata

        parameters = {}
        for key, value in self.parameters.items(): #make copy
            if key != 'branch':
                parameters[key] = value
        parameters['-t'] = sourcedata + '.' + set + '.txt'
        print >>sys.stderr, "STARTING DECODER FOR ", repr(parameters)
        print >>sys.stderr,"  stdout="+self.dir + '/decode.out , stderr='+self.dir + '/decode.err'
        self.startcommand(PBMBMTDIR + '/pbmbmt-decode', EXPDIR + '/' + set, stdout, stderr, **parameters)

    def score(self):
        try:
            if self.process.returncode != 0:
                print >>sys.stderr,"*** UNABLE TO DECODE! DECODER EXITED WITH ERROR CODE! Check " + self.dir + "/decode.err ! ***"
                return 0
        except:
            print >>sys.stderr,"*** NO DECODER STARTED, ATTEMPTING TO SCORE ANYWAY ***"
            pass

        print >>sys.stderr,"SCORING FOR ", repr(self.parameters)

        if not os.path.isdir(self.dir):
            print >>sys.stderr,"*** UNABLE TO SCORE! DIRECTORY " + self.dir + " DOES NOT EXIST! ***"
            return 0


        #run scorer
        os.system('python ' + MATREXDIR + '/eval/sgmize.py tst name src trg docid sysid ' + self.dir + '/decode.out > ' + self.dir + '/decode.out.sgm')


        sourcedata, refdata, set = self.inputdata
        sourcesgm = EXPDIR + '/' + sourcedata + '.' + set + '.txt.sgm'
        targetsgm = self.dir + '/decode.out.sgm'
        refsgm = EXPDIR + '/' + refdata + '.' + set + '.txt.sgm'
        scorefile = self.dir + '/decode.score'
        scoreerr = self.dir + '/score.err'

        print >>sys.stderr,"  scorefile="+ scorefile + " , sourcesgm="+sourcesgm +" , targetsgm="+targetsgm + " , refsgm="+refsgm


        if not os.path.exists(sourcesgm):
            os.system('python ' + MATREXDIR + '/eval/sgmize.py src name src trg docid sysid ' + EXPDIR + '/' + set + '/' + sourcedata+ '.' + set + '.txt > ' +  EXPDIR + '/' + sourcedata + '.' + set + '.txt.sgm 2>> ' + scoreerr)
        if not os.path.exists(refsgm):
            os.system('python ' + MATREXDIR + '/eval/sgmize.py ref name src trg docid sysid ' + EXPDIR + '/' + set + '/' + refdata+ '.' + set + '.txt > ' +  EXPDIR + '/' + refdata + '.' + set + '.txt.sgm 2>> ' + scoreerr)


        #WER
        f = open(scorefile,'w')
        f.write("DECODE SCORE\n" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\nWER\n')
        f.close()

        os.system('perl ' + MATREXDIR + '/eval/WER_v01.pl -r ' + refsgm + ' -t ' + targetsgm + ' -s ' + sourcesgm + ' >> ' + scorefile + ' 2>> ' + scoreerr)

        #PER
        f = open(scorefile,'a')
        f.write("PER\n")
        f.close()
        os.system('perl ' + MATREXDIR + '/eval/PER_v01.pl -r ' + refsgm + ' -t ' + targetsgm + ' -s ' + sourcesgm + ' >> ' + scorefile + ' 2>> ' + scoreerr)

        #BLEU
        f = open(scorefile,'a')
        f.write("BLEU\n")
        f.close()
        os.system('perl ' + MATREXDIR + '/eval/bleu-1.04.pl -r ' + refsgm + ' -t ' + targetsgm + ' -s ' + sourcesgm + ' -ci >> ' + scorefile + ' 2>> ' + scoreerr)


        #METEOR
        cmd = 'perl -I ' + MATREXDIR + '/meteor-0.6/' + ' ' + MATREXDIR + '/meteor-0.6/meteor.pl -s sysid1 -t ' + targetsgm + ' -r ' + refsgm + ' --modules "exact"'
        f = open(scorefile,'a')
        f.write("METEOR\n")
        f.write("Command line: " + cmd+"\n")
        f.close()
        os.system(cmd + ' >> ' + scorefile + ' 2>> ' + scoreerr)

        #NIST & BLEU
        f = open(scorefile,'a')
        f.write("MTEVAL\n")
        f.close()
        os.system('perl ' + MATREXDIR + '/mteval-v11b.pl -r ' + refsgm + ' -t ' + targetsgm + ' -s ' + sourcesgm + ' >> ' + scorefile + ' 2>> ' + scoreerr)

        #TER
        f = open(scorefile,'a')
        f.write("TER\n")
        f.close()
        os.system('java -jar ' + MATREXDIR + '/tercom.jar -r ' + refsgm + ' -h ' + targetsgm + ' >> ' + scorefile + ' 2>> ' + scoreerr) #' -s ' + EXPDIR + '/' + sourcedata + '.' + set + '.txt' + ' -n sum 

        #read scores
        self.per = 0
        self.wer = 0
        self.bleu = 0
        self.meteor = 0
        self.nist = 0
        self.ter = 0
        f = open(self.dir+"/decode.score")  
        for line in f.readlines():
                if line[0:11] == "WER score =":
                        try:
                            self.wer = float(line[12:20].strip())
                        except:
                            print >>sys.stderr, "ERROR: Unable to score!!!"
                            return 0
                if line[0:11] == "PER score =":
                        try:
                            self.per = float(line[12:20].strip())
                        except:
                            print >>sys.stderr, "ERROR: Unable to score!!!"
                            return 0
                if line[0:12] == "NIST score =":
                        self.nist = float(line[13:21].strip())
                        if self.bleu < 0.01 and line[21:33] == "BLEU score =":
                            try:
                                self.bleu = float(line[34:40].strip())
                            except:
                                print >>sys.stderr, "Couldn't get fallback bleu score"
                                pass
                if line[0:6] == "Score:":
                        self.meteor = float(line[7:].strip())
                if line[0:9] == "BLEUr1n4," and self.bleu <= 0.01:
                        try:
                                self.bleu = float(line[10:].strip())
                        except:
                                print >>sys.stderr, "(BLEU score too low!)"
                if line[0:10] == "Total TER:":
                        self.ter = float(line[11:].strip().split(' ')[0])

        f.close()

        return self.bleu #return only bleu for now

    def scoreoutput(self,table=True,oneliner=True,latex=True):
        #make sure to call score first
        if 'name' in dir(self):
           name = self.name
        else:
           name = self.label
        s =  "EXPERIMENT: " + name + "\n"
        s += "DIRECTORY:  " + self.dir + "\n"
        s += "PARAMETERS: " + " ".join([ x + ' ' + str(y) for x,y in self.parameters.items() ]) + "\n"
        if table: s += self.scoretable() + "\n"
        if oneliner: s += "ONELINER:   " + self.scorerow() + "\n"
        if latex:    s += "LATEX:      " + self.scorerowlatex() + "\n"
        return s


    def scoretable(self):
        return "BLEU SCORE:   " + str(round(self.bleu,4)) + "\nMETEOR SCORE: " + str(round(self.meteor,4)) + "\nNIST SCORE:   " + str(round(self.nist,4)) + "\nTER SCORE:    " + str(round(self.ter,2)) + "\nWER SCORE:    " + str(round(self.wer,2)) + "\nPER SCORE:    " + str(round(self.per,2))

    def scorerow(self):
       if 'name' in dir(self):
           name = self.name
       else:
           name = self.label
       return name + " " + str(round(self.bleu,4)) + " " + str(round(self.meteor,7)) + " " + str(round(self.nist,4)) + " " + str(round(self.ter,4)) + " " + str(round(self.wer,4)) + " " + str(round(self.per,4))

    def scorerowlatex(self):
       if 'name' in dir(self):
           name = self.name
       else:
           name = self.label
       return name + " & $" + str(self.bleu) + "$ & $" + str(self.meteor) + "$ & $" + str(self.nist) + "$ & $" + str(self.ter) + "$ & $" + str(self.wer) + "$ & $" + str(self.per) + "$ \\\\"


    def delete(self):
        assert len(self.dir) > 3
        shutil.rmtree(self.dir,True)

    @staticmethod
    def sample(data, size):
        """Generate a sample. This is a rather complex procedure, as we need to make a sample test data, the reference. And then we need to regenerate test instances and rerun the classifier!"""

        print >>sys.stderr,"SAMPLING, size=", size

        #Generate samples
        inputdata, refdata,set = data


        print >>sys.stderr, "\tSampling test data"

        f = open(EXPDIR + '/' + set + '/' + inputdata + '.' + set + '.txt','r')
        lines = f.readlines()
        f.close()
        selection = random.sample(range(0,len(lines)), size)

        newinputdata = inputdata + '-' + str(size)  #new filename
        f = open(EXPDIR + '/' + set + '/' + newinputdata + '.' + set + '.txt' ,'w')
        for i in selection:
            f.write(lines[i])
        f.close()

        print >>sys.stderr,"\tSampling reference data"

        f = open(EXPDIR + '/' + set + '/' + refdata + '.' + set + '.txt','r')
        lines = f.readlines()
        f.close()
        newrefdata = refdata + '-' + str(size)  #new filename
        f = open(EXPDIR + '/' + set + '/' + newrefdata + '.' + set + '.txt' ,'w')
        for i in selection:
            f.write(lines[i])
        f.close()

        #make a link to the phrasetable
        if not os.path.exists(EXPDIR + '/' + newinputdata + '.train.phrasetable'):
            os.symlink(EXPDIR + '/' + inputdata + '.train.phrasetable',EXPDIR + '/' + newinputdata + '.train.phrasetable')

        try:
            os.mkdir(EXPDIR + '/' + set + '/' + newinputdata)
        except:
            pass

        print >>sys.stderr,"\tCopying training files"

        #copy trainfiles, so we don't need to regenerate these
        for f in glob.glob(EXPDIR + '/' + set + '/' + inputdata + '/' + inputdata + '.train.*.inst'):
            shutil.copyfile(f, f.replace(inputdata, newinputdata) )

        newdata = (newinputdata, newrefdata, set)

        print >>sys.stderr,"\tRegenerating test instances"
        #regenerate testfiles
        PBMBMTTestGenExperiment(newdata).run()

        print >>sys.stderr,"\tRerunning classifier"

        #retrain + test
        PBMBMTClassifierExperiment(newdata).run()


        #sgmlize both for scoring
        os.system('python ' + MATREXDIR + '/eval/sgmize.py src name src trg docid sysid ' + EXPDIR + '/' + set + '/' +  newinputdata+ '.' + set + '.txt > ' +  EXPDIR + '/' + newinputdata + '.' + set + '.txt.sgm')
        os.system('python ' + MATREXDIR + '/eval/sgmize.py ref name src trg docid sysid ' + EXPDIR + '/' + set + '/' + newrefdata+ '.' + set + '.txt > ' +  EXPDIR + '/' + newrefdata + '.' + set + '.txt.sgm')

        return (newinputdata, newrefdata, set)


def usage():
    print >> sys.stderr,"Syntax: pbmbmt [options] -- source reference set (extra-label)"
    print >> sys.stderr,"Override default experiment directory:"
    print >> sys.stderr,"\t--expdir=<dir>"
    print >> sys.stderr,"Enable components: (by default all are enabled)"
    print >> sys.stderr,"\t-G   Generation only"
    print >> sys.stderr,"\t-T   Classifier only"
    print >> sys.stderr,"\t-D   Decoding and scoring only"
    print >> sys.stderr,"\t-S   Scoring only"
    print >> sys.stderr,"\t-Dbranch 1     Enable decoder branching (classifier output is read from a common directory, but decoder output is branched off to another output directory, with an extra label containing the decoder features"
    print >> sys.stderr,"\t-Tparamsearch  Read settings from *.bestsetting files (as generated by paramsearch), supports different settings for different classifiers!"
    print >> sys.stderr,"Instance generation parameters: (all start with -G* or --G*)"
    print >> sys.stderr,"\t(See pbmbmt-make-instances for a full list, don't forget to prepend -G!)"
    print >> sys.stderr,"Classifier parameters: (all start with -T* or --T*)"
    print >> sys.stderr,"\t-Ta [0=IB1,1=IGTree,3=IB2,4=TRIBL2] - Timbl Algorithm"
    print >> sys.stderr,"\t-Tm [string] - feature metrics"
    print >> sys.stderr,"\t-Tw [int/string] - weighting"
    print >> sys.stderr,"\t-Tk [int]    - number of nearest neighbours"
    print >> sys.stderr,"\t(See Timbl -h for a full list, don't forget to prepend -T!)"
    print >> sys.stderr,"Decoder parameters:"
    print >> sys.stderr,"\t-Db [beamsize=1] - Beamsize for core decoder"
    print >> sys.stderr,"\t-Df [beamsize=20] - Beamsize for fragmentation search"
    print >> sys.stderr,"\t(See pbmbmt-decoder for a full list, don't forget to prepend -D!)"
    print >> sys.stderr,"\t-DD [DISTORTION CONSTANT=0.25] - The lower the value, the less likely the decoder is to swap the location of fragments"
    print >> sys.stderr,"\t-DB [PTRANSLATION_THRESHOLD=0.8] - Only hypothesis fragments with a translation probability higher or equal than B% of the maximum translation probability will be considered. "
    print >> sys.stderr,"\t-DW [PTRANSLATION_WEIGHT=3] - Translation probability is raised to the W'th power to give stronger weight"
    print >> sys.stderr,"\t-DS [MAX_SWAP_DISTANCE=2] - Maximum swap distance in one expansion"
    print >> sys.stderr,"\t-DX - Disable further decoding, simply return initial hypothesis  (produces quick but poorer results)"
    print >> sys.stderr,"\t-DQ - Use simpler solution searcher, simply grabbing the solution with the highest score instead of taking into account equivalent results accross fragmentations"
    print >> sys.stderr,"\t-DE - Do *NOT* use the entropy based score function for fragmentation search"
    print >> sys.stderr,"\t-Dw - Word-based only (only works in multi-classifier mode)"
    print >> sys.stderr,"\t-DL [port] - Use a Language Model server the specified port"
    print >> sys.stderr,"\t--Dwopr [port]           - Use WOPR server on specified port"
    print >> sys.stderr,"\t--Dsimplelm [filename]   - Use simpler Language Model instead of SRILM or WOPR"
    print >> sys.stderr,"\t--Dsrilm [filename]      - Use SRILM"

if __name__ == "__main__":
    print >>sys.stderr,"PBMBMT - Phrase-Based Memory-Based Machine Translator"
    print >>sys.stderr,"     by Maarten van Gompel"
    print >>sys.stderr, "     Induction of Linguistic Knowledge Research Group"
    print >>sys.stderr,"     Tilburg University"
    print >>sys.stderr,"-----------------------------------------------------"
    parameters = {}
    parameters['generation'] = {}
    parameters['classifier'] = {}
    parameters['decoder'] = {}

    args = []

    genonly = False
    timblonly = False
    decodeonly = False
    scoreonly = False

    optionsdone = False

    for i in range(1,len(sys.argv)):
        field = sys.argv[i]
        if field == '--':
            optionsdone = True
        elif not optionsdone and field[0] == '-' or field[0] == '+':
            if field[1] == '-':
                optionprefix = '--'
                optiontype = field[2]
                eq = field.find('=')
                if optiontype in ['G','T','D','S']:
                    if eq == -1:
                        option = field[3:]
                    else:
                        option = field[3:eq+1]
                        optionvalue = field[eq+1:]
                else:
                    if eq == -1:
                        option = field[2:]
                    else:
                        option = field[2:eq]
                        optionvalue = field[eq+1:]
            else:
                optionprefix = '-'
                optiontype = field[1]
                eq = field.find('=')
                if eq == -1:
                    option = field[2:]
                else:
                    option = field[2:eq+1]
                    optionvalue = field[eq+1:]
            
            if eq == -1: #only if no equal sign was found
                if i+1 < len(sys.argv) and sys.argv[i+1][0] != '-':
                    optionvalue = sys.argv[i+1]
                    i += 1
                else:
                    optionvalue = True

            if optiontype == 'G':
                if option:
                    parameters['generation'][optionprefix+option] = optionvalue
                else:
                    genonly = True
            elif optiontype == 'T':
                if option:
                    parameters['classifier'][optionprefix+option] = optionvalue
                else:
                    timblonly = True
            elif optiontype == 'D':
                if option:
                    parameters['decoder'][optionprefix+option] = optionvalue
                else:
                    decodeonly = True
            elif optiontype == 'S':
                if option:
                    parameters['decoder'][optionprefix+option] = optionvalue
                else:
                    decodeonly = True
                    scoreonly = True
            elif option == 'expdir':
                EXPDIR = optionvalue
            else:
                print >>sys.stderr, "ERROR: Invalid option:", field
                usage()
                sys.exit(1)
        elif i == 1:
            args.append(field)
            optionsdone = True
        elif optionsdone:
            args.append(field)


    if len(args) < 3:
         print >>sys.stderr, "ERROR: Too few arguments"
         usage()
         sys.exit(1)

    source = args[0]
    print >>sys.stderr, "SOURCE:    ", source
    ref = args[1]
    print >>sys.stderr, "REFERENCE: ", ref
    set = args[2]
    print >>sys.stderr, "SET:       ", set

    if len(args) == 4:
        label = args[3]
        parameters['generation']['-o'] = label
        parameters['classifier']['infix'] = label
        parameters['decoder']['-o'] = label
        print >>sys.stderr, "LABEL:     ", label

    if '-a' in parameters['classifier'] and parameters['classifier']['-a'] == '0':
        parameters['classifier']['+D'] = True

    #use alignment probability in classifier:
    if '-s' in parameters['generation'] or '-s' in parameters['classifier']:
        #if one is set, the other must be too
        parameters['generation']['-s'] = True
        parameters['classifier']['-s'] = True
    #use alignment probability in decoder:
    if '-S' in parameters['generation'] or '-Z' in parameters['decoder']:
        parameters['classifier']['-?'] = 1 #ignore first column #TODO: What is the Timbl option for this???
        parameters['decoder']['-Z'] = True
    if '-a' in parameters['classifier'] and parameters['classifier']['-a'] == '1':
        #IGTree need +D for +vdb
        parameters['classifier']['+D'] = True

    if not genonly and not timblonly and not decodeonly:
        exp = PBMBMTExperiment( (source,ref,set), **parameters)
        exp.run()
        print exp.decodeexperiment.score()
    else:
        if genonly:
            exp = PBMBMTInstanceGenerationExperiment( (source,set), **parameters['generation'])
            exp.run()
        if timblonly:
            exp = PBMBMTClassifierExperiment( (source,set), **parameters['classifier'])
            exp.run()
        if decodeonly:
            if '-branch' in parameters['decoder'] and parameters['decoder']['-branch']:
                parameters['decoder']['branch'] = True
                del parameters['decoder']['-branch']
                print >>sys.stderr,"DECODER BRANCHING ENABLED"
            elif '--branch' in parameters['decoder'] and parameters['decoder']['--branch']:
                parameters['decoder']['branch'] = True
                del parameters['decoder']['--branch']
                print >>sys.stderr,"DECODER BRANCHING ENABLED"
            else:
                print >>sys.stderr,"DECODER BRANCHING DISABLED"
                parameters['decoder']['branch'] = False
            exp = PBMBMTDecodeExperiment( (source,ref, set), **parameters['decoder'])
            if not scoreonly:
                exp.run()
            exp.score()
            print >>sys.stderr, "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - "
            print exp.scoreoutput()
            print "==========================================================="


