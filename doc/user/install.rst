.. vim: set filetype=rst

============================
Installing and running khmer
============================

You'll need a 64-bit operating system, internet access, and Python
2.7.x OR Python 3.3 or greater.

Build requirements
------------------

OS X 
^^^^

#) From a terminal download the virtualenv package and create a
   virtual environment with it::

      curl -O https://pypi.python.org/packages/source/v/virtualenv/virtualenv-1.11.6.tar.gz
      tar xzf virtualenv*
      cd virtualenv-*; python2.7 virtualenv.py ../khmerEnv; cd ..
      source khmerEnv/bin/activate

Linux
^^^^^

#) Install the python development environment, virtualenv, pip, gcc, and g++.

   - On recent Debian and Ubuntu this can be done with::

         sudo apt-get install python2.7-dev python-virtualenv python-pip gcc \
                g++

   - For RHEL6::

         sudo yum install -y python-devel python-pip git gcc gcc-c++ make
         sudo pip install virtualenv   

#) Create a virtualenv and activate it::

      cd a/writable/directory/
      python2.7 -m virtualenv khmerEnv
      source khmerEnv/bin/activate

   Linux users without root access can try the OS X instructions above.

Installing khmer inside the virtualenv
--------------------------------------

#) Use pip to download, build, and install khmer and its dependencies::

      pip2 install khmer

#) The scripts are now in the ``env/bin`` directory and ready for your
   use. You can directly use them by name, see :doc:`scripts`.

#) When returning to khmer after installing it you will need to
   reactivate the virtualenv first::

      source khmerEnv/bin/activate

Run the tests
^^^^^^^^^^^^^

After installing you can run the embedded test suite::

      nosetests khmer --attr '!known_failing'

If the nosetests binary isn't installed then::

      pip2 install khmer[tests]
      nosetests khmer --attr '!known_failing'
