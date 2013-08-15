#!/usr/bin/env python
import logging
from mpiutil.mpimanager import MPIManager
from mpi4py import MPI
import code, traceback, signal

def debug(sig, frame):
    """Interrupt running process, and provide a python prompt for
    interactive debugging."""
    d={'_frame':frame}         # Allow access to frame object.
    d.update(frame.f_globals)  # Unless shadowed by global
    d.update(frame.f_locals)

    i = code.InteractiveConsole(d)
    message  = "Signal recieved : entering python shell.\nTraceback:\n"
    message += ''.join(traceback.format_stack(frame))
    i.interact(message)

def listen():
    signal.signal(signal.SIGUSR1, debug)  # Register handler

if __name__ == "__main__":
    listen()

    formatter = logging.Formatter("%(asctime)s - %(name)s %(mpi_rank)d/%(mpi_size)d %(funcName)s - %(levelname)s - %(message)s")
    mpi_manager=MPIManager(range(20))
    mpi_manager.setFormatter(formatter)
    mpi_manager.setLevel(logging.DEBUG)
        
    LOG=logging.getLogger('mpi_util')
    LOG.setLevel(logging.DEBUG)
    LOG.addHandler(mpi_manager)

    if not mpi_manager.run():
        print('worker %d'%MPI.COMM_WORLD.Get_rank())
        for a in mpi_manager:
            LOG.debug('item %d',a)
        mpi_manager.send_done()
    print('main thread done %d'%MPI.COMM_WORLD.Get_rank())
