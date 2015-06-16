Hot to set-up DALEK on C2PAP
============================

1. Set language to English. This is required even if you speak German or anything else since parts of IPython Parallel relies on Linux commands being in English. To do this add the following line to your ~/.bashrc::

    export LANGUAGE="en_US"


#. Download and set-up Anaconda and TARDIS by following instructions `here <https://tardis.readthedocs.org/en/latest/installation.html>`_.

#. Create a new ipython profile::

    $ ipython profile create --parallel --profile=pbs

#. Edit ~/.ipython/profile_pbs/ipcluster_config.py file to add the following lines at the end:
   
   1. This is to make sure that ipython parallel can catch the job id from the output of batch submit command::

       c.PBSLauncher.job_id_regexp = 'mgmt\.\d+'
   #. These tell the launcher to use LoadLeveler commands to submit and cancel jobs::

       c.PBSLauncher.submit_command = ['llsubmit']
       c.PBSLauncher.delete_command = ['llcancel']
   #. This is used to set up launchers for ipcluster controller and engines::

       c.IPClusterStart.controller_launcher_class = 'LocalControllerLauncher'
       c.IPClusterEngines.engine_launcher_class = 'PBSEngineSetLauncher'
       c.PBSEngineSetLauncher.batch_template = """ 
       #@ job_type = parallel
       #@ class = parallel
       #@ group = pr94se
       #
       #@ blocking = unlimited
       #@ total_tasks = {n}
       #@ node_usage = shared
       #
       #@ wall_clock_limit = 48:00:00
       #@ resources = ConsumableCpus({n})
       #@ output = /gpfs/work/pr94se/di73kuj/$(jobid).out
       #@ error  = /gpfs/work/pr94se/di73kuj/$(jobid).err
       #@ queue
       
       export PATH="/home/hpc/pr94se/di73kuj/anaconda/bin:$PATH"
       export LANGUAGE="en_US"
       source activate tardis
       mpiexec -n {n} ipengine --profile-dir={profile_dir}
       """

#. Edit ~/.ipython/profile_pbs/ipcontroller_config.py file to add the following line at the end::

    c.HubFactory.ip = '*'


#. Edit ~/.ipython/profile_pbs/ipcontroller_config.py file to add the following line at the end::

    c.EngineFactory.timeout = 1000.0

#. Install DALEK::

    $ git clone https://github.com/tardis-sn/dalek.git
    $ cd dalek
    $ python setup.py install

#. Run ipcluster::

    $ ipcluster start -n 8 --profile=pbs

#. Test the engines are running::

    $ ipython --profile=pbs
    In [1]: from IPython.parallel import Client
    In [2]: rc = Client()
    In [3]: rc.ids
    Out[3]: [0, 1, 2, 3, 4, 5, 6, 7]
