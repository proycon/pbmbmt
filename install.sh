#!/bin/bash

echo "Looking for git"
if [ -z "$GIT" ]; then GIT=`which git`; fi
if [ -z "$GIT" ]; then
    echo "Git not found! Please install git first"  >&2
    exit 1
fi

echo "Looking for wget"
if [ -z "$WGET" ]; then WGET=`which wget`; fi
if [ -z "$WGET" ]; then
    echo " Wget not found! Please install wget first"  >&2
    exit 1
fi


echo "Looking for python"
if [ -z "$PYTHON" ]; then PYTHON=`which python`; fi
if [ -z "$PYTHON" ]; then
    echo "************************************************************************************">&2
    echo "Python is not found, please install python 2.5 or above (but < 3.0)"  >&2
    echo "************************************************************************************">&2
    exit 1
fi
    echo "Timbl found: $TIMBL"

echo "Looking for perl"
if [ -z "$PERL" ]; then PERL=`which perl`; fi
if [ -z "$PERL" ]; then
    echo "************************************************************************************">&2
    echo "WARNING: Perl is not found but is required for running the evaluation scripts. We will continue nevertheless but evaluation will fail!"  >&2
    echo "************************************************************************************">&2
    sleep 5
fi


echo "Looking for java"
if [ -z "$JAVA" ]; then PERL=`which java`; fi
if [ -z "$JAVA" ]; then
    echo "************************************************************************************">&2
    echo "WARNING: Java is required for the TER evaluation metric but was not found, we will continue but you won't have TER scores until you install it"  >&2
    echo "************************************************************************************">&2
    sleep 5
fi


echo "Looking for 3rd-party evaluation scripts (Matrex, NIST, METEOR, TER)"
if [ -z "$MTEVALSCRIPTS" ]; then MTEVALSCRIPTS='mtevalscripts'; fi
if [ -d $MTEVALSCRIPTS ]; then
    echo "Found: $MTEVALSCRIPTS"
else
    echo "Downloading..."
    wget http://ilk.uvt.nl/~mvgompel/mtevalscripts.tar.gz
    if [ $? != 0 ]; then
        echo "Unable to download http://ilk.uvt.nl/~mvgompel/mtevalscripts.tar.gz ! Contact the author!"
        exit 1
    fi
    tar -xzf mtevalscripts.tar.gz
    MTEVALSCRIPTS='mtevalscripts'
fi

echo "Looking for PyNLPl..."
if [ -z "$PYNLPL" ]; then
   PYNLPL='pynlpl'; 
   if [ -d $PYNLPL ]; then
       echo "Found: $PYNLPL"
   else
       echo "Downloading..."
       git clone git://github.com/proycon/pynlpl.git
       rm -Rf pynlpl/.git
   fi
else
   if [ -d $PYNLPL ]; then
        ln -s $PYNLPL pynlpl
   else
        echo "Specified PyNLPl directory does not exist">%2
        exit 1
   fi
fi



echo "Looking for Timbl..."
if [ -z "$TIMBL" ]; then TIMBL=`which timbl`; fi
if [ -z "$TIMBL" ]; then
    echo "Downloading..."
    mkdir tmp
    wget http://ilk.uvt.nl/downloads/pub/software/timbl-6.3.0.tar.gz
    echo "Extracting..."
    tar -xzf timbl-6.3.0.tar.gz
    cd timbl-6.3.0

    echo -n "Where do you want to install Timbl? [/usr/local/] "
    read $TIMBLINSTALLDIR
    mkdir -p $TIMBLINSTALLDIR

    ./configure --prefix=$TIMBLINSTALLDIR
    if [ $? != 0 ]; then
        echo "Error, timbl configuration failed! This might be due to missing dependencies" >&2
        exit 1
    fi
    make
    if [ $? != 0 ]; then
        echo "Error, timbl compilation failed!" >&2
        exit 1
    fi
    make install
    if [ $? != 0 ]; then
        echo "Error, timbl installation failed!" >&2
        exit 1
    else
        TIMBL="$TIMBLINSTALLDIR/bin/Timbl"
        echo "Timbl installed: $TIMBL"
    fi
    
    cd ../..
    rm -Rf tmp
else
    echo "Timbl found: $TIMBL"
fi


