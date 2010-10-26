#!/bin/bash
#   PBMBMT installation script
#       by Maarten van Gompel



echo "This script is still under development, please don't use it yet until fully tested!!"




echo "PBMBMT is licensed under the GNU Public License v3. The full text is available in the LICENSE file"
echo -n "Dependencies Timbl and PyNLPl are equally licensed under GPLv3. Dependency SRILM is licensed under the SRILM Research Community license. These dependencies will be downloaded automatically if not available yet. Do you agree to this and to all license conditions? [y/n] "
read AGREE
if [ "$AGREE" != "y" ]; then
    echo "Aborting..."  >&2
    exit 1
fi




echo "Looking for git"
if [ -z "$GIT" ]; then GIT=`which git | tr -d '\n'`; fi
if [ -z "$GIT" ]; then
    echo "Git not found! Please install git first"  >&2
    exit 1
else
    echo "...ok"
fi

echo "Looking for wget"
if [ -z "$WGET" ]; then WGET=`which wget | tr -d '\n'`; fi
if [ -z "$WGET" ]; then
    echo "Wget not found! Please install wget first"  >&2
    exit 1
else
    echo "...ok"
fi


echo "Looking for python"
if [ -z "$PYTHON" ]; then PYTHON=`which python | tr -d '\n'`; fi
if [ -z "$PYTHON" ]; then
    echo "************************************************************************************">&2
    echo "Python is not found, please install python 2.5 or above (but < 3.0)"  >&2
    echo "************************************************************************************">&2
    exit 1
else
    echo "...ok"
fi

echo "Looking for perl"
if [ -z "$PERL" ]; then PERL=`which perl  | tr -d '\n'`; fi
if [ -z "$PERL" ]; then
    echo "************************************************************************************">&2
    echo "WARNING: Perl is not found but is required for running the evaluation scripts. We will continue nevertheless but evaluation will fail!"  >&2
    echo "************************************************************************************">&2
    sleep 5
else
    echo "...ok"
fi


echo "Looking for java"
if [ -z "$JAVA" ]; then JAVA=`which java | tr -d '\n'`; fi
if [ -z "$JAVA" ]; then
    echo "************************************************************************************">&2
    echo "WARNING: Java is required for the TER evaluation metric but was not found, we will continue but you won't have TER scores until you install it"  >&2
    echo "************************************************************************************">&2
    sleep 5
else
    echo "...ok"
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
    rm mtevalscripts.tar.gz
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
if [ -z "$TIMBL" ]; then TIMBL=`which Timbl | tr -d '\n'`; fi
if [ -z "$TIMBL" ]; then
    echo "Downloading..."
    mkdir tmp
    cd tmp
    wget http://ilk.uvt.nl/downloads/pub/software/timbl-6.3.0.tar.gz
    echo "Extracting..."
    tar -xzf timbl-6.3.0.tar.gz
    cd timbl-6.3.0

    echo -n "Where do you want to install Timbl? [/usr/local/] "
    read TIMBLINSTALLDIR
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
if [ -f pynlpl/lm/srilmcc.so ]; then
    echo "Found!"
else

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

    echo "Downloading SRILM base code (full version available at: http://www-speech.sri.com/projects/srilm/), licensed under SRILM Research Community License)"
    mkdir tmp
    cd tmp

    wget http://ilk.uvt.nl/~mvgompel/srilm-5.10-pymod.tar.gz #Note that this SRILM is downloaded only for compilation of the python module and then removed. If you want to use SRILM for any other purposes, download it from its official site at http://www-speech.sri.com/projects/srilm/  !
    tar -xvzf srilm-5.10-pymod.tar.gz
    cd srilm-5.10-pymod
    export SRILM=`pwd`
    MACHINE_TYPE="i686" #also for x86_64 !

    make MACHINE_TYPE=$MACHINE_TYPE NO_TCL=X
    if [ $? != 0 ]; then
        echo "Error, SRILM compilation failed! Please inspect error output." >&2
        exit 1
    fi

    export SRILMLIBS=$SRILM/lib/$MACHINE_TYPE
    
    cd ../../
    cd pynlpl/lm
    ln -s ../../tmp/srilm-5.10-pymod srilm

    g++ -fPIC -shared -I/usr/include/python$PYTHONVERSION -lpython$PYTHONVERSION -I$SRILM/src -I$SRILM/include -lboost_python srilm.cc $SRILMLIBS/liboolm.a $SRILMLIBS/libdstruct.a $SRILMLIBS/libmisc.a -o srilmcc.so #this assumes python libraries are in /usr/include/python !
    if [ $? != 0 ]; then
        echo "Error, Compilation of SRILM Python Module compilation! May be due to missing libboost? Please inspect error output." >&2
        exit 1
    fi

    rm srilm

    cd ../..
    rm -Rf tmp

fi



echo "All done!"
