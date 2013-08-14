import os
import stat
from datetime import datetime
from setuptools import setup

def read(fname):
	    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def most_recent_mod(directory):
	mod=0;
	for dirpath, dirnames, filenames in os.walk(directory): 
		for filename in filenames:
			fname=os.path.join(dirpath,filename)
			stats=os.stat(fname)
			mtime=stats[stat.ST_MTIME]
			mod=max(mod,stats[stat.ST_MTIME])
	return mod

src='src/mpiutil'

ver=datetime.fromtimestamp(most_recent_mod(src)).strftime('%Y.%m.%d.%H.%M')

setup(
	name='mpiutil',
	install_requires=['mpi4py>=1.3'],
	description='A python module userfule for working with MPI',
	author='Robert I. Petersen',
	author_email='rpetersen@ucsd.edu', 
	version=ver,
	package_dir={'mpiutil': src},
	packages=['mpiutil'], 
	license='GPL 2.0', 
	classifiers=[
'Development Status :: 4 - Beta',
'Intended Audience :: Developers',
'License :: OSI Approved :: GNU General Public License (GPL)',
'Programming Language :: Python'
	],
	long_description=read('README')
)
