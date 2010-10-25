
#Set this to the place where you extracted the pbmbmt directory
PBMBMTDIR="/home/<username>/pbmbmt"

#Point this to where the Matrex evaluation package is installed
MATREXDIR=PBMBMTDIR + "/Matrex"

#This is where all experiment results will be stored
EXPDIR=PBMBMDIR + "/experiments"

#Point this to whereever Timbl resides (may also be /usr/bin/Timbl ?)
TIMBL="/usr/local/bin/Timbl" 

#Remove this line once you finish setting all of the above:
raise Exception("Please configure PBMBMT first, edit config.py")
