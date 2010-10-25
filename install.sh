#!/bin/bash

echo "This script is still under development, please don't use it yet until fully tested"
exit 1

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



echo "Looking for SRILM Python module..."
if [ -f pyblpl/lm/srilmcc.so ]; then
    echo "Found!"
else
    echo "Downloading SRILM base code (full version available at: http://www-speech.sri.com/projects/srilm/), licensed under SRILM Research Community License)"
    mkdir tmp

    wget http://ilk.uvt.nl/~mvgompel/srilm-5.10-pymod.tar.gz
    tar -xvzf srilm-5.10-pymod.tar.gz
    cd srilm-5.10-pymod
    export SRILM=`pwd`
    MACHINE_TYPE="i686"
    make MACHINE_TYPE=$MACHINE_TYPE NO_TCL=X
    export SRILMLIBS=$SRILM/lib/$MACHINE_TYPE
    
    if [ -d /usr/include/python2.6 ]; then
        PYTHONVERSION="2.6"
    elif [ -d /usr/include/python2.7 ]; then
        PYTHONVERSION="2.7"
    elif [ -d /usr/include/python2.5 ]; then
        PYTHONVERSION="2.5"
    else
        echo "Unable to find python headers in /usr/include/python2.5 / 2.6 / 2.7. "
        exit 1
    fi

    g++ -fPIC -shared -I/usr/include/python$PYTHONVERSION -lpython$PYTHONVERSION -I$SRILM/src -I$SRILM/include -lboost_python srilm.cc $SRILMLIBS/liboolm.a $SRILMLIBS/libdstruct.a $SRILMLIBS/libmisc.a -o srilmcc.so #this assumes python libraries are in /usr/include/python !

    cd ..
    rm -Rf tmp

fi

if [ -z "$TIMBL" ]; then TIMBL=`which timbl`; fi
if [ -z "$TIMBL" ]; then

else
    echo "Timbl found: $TIMBL"
fi

