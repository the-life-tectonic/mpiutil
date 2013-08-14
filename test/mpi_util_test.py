#!/usr/bin/env python
import logging
from mpiutil.mpilogging import MPILogger, MPIHandler
from mpiutil.collections import MPIIterator
import time

if __name__ == "__main__":
    logging.setLoggerClass(MPILogger)

    formatter = logging.Formatter("%(asctime)s - %(name)s %(mpi_rank)d/%(mpi_size)d %(funcName)s - %(levelname)s - %(message)s")
    screen_handler=logging.StreamHandler()
    screen_handler.setFormatter(formatter)
    screen_handler.setLevel(logging.DEBUG)
    mpi_handler=MPIHandler(screen_handler)
    mpi_handler.setLevel(logging.DEBUG)

    LOG=logging.getLogger('mpi_util')
    LOG.setLevel(logging.DEBUG)
    LOG.addHandler(mpi_handler)

    for a in MPIIterator(range(10)):
        LOG.debug('item %d',a)
        time.sleep(.5)
