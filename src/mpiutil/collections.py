import threading
from mpi4py import MPI

class MPIIterator(threading.Thread):
    TAG_ITERATOR=4570
    NEXT=0
    STOP_ITERATION=1

    def __init__(self,items,source_rank=0,comm=MPI.COMM_WORLD):
        self.source_rank=0
        self.mpi_comm=comm
        self.mpi_rank=comm.Get_rank()
        self.mpi_size=comm.Get_size()
        super(MPIIterator, self).__init__()
        if self.mpi_rank==self.source_rank:
            self._iter=iter(items);
            self.start()

    def __iter__(self):
        return self

    def next(self):
        if self.mpi_rank==self.source_rank:
            return self._iter.next()
        else:
            self.mpi_comm.send({'type':MPIIterator.NEXT},dest=self.source_rank,tag=MPIIterator.TAG_ITERATOR)
            data = self.mpi_comm.recv(source=self.source_rank, tag=MPIIterator.TAG_ITERATOR)
            if data['type']==MPIIterator.STOP_ITERATION:
                raise StopIteration()
            elif data['type']==MPIIterator.NEXT:
                return data['value']

    def run(self):
        mpi_stopped=0
        while True:
            status=MPI.Status()
            self.mpi_comm.Probe(source=MPI.ANY_SOURCE, tag=MPIIterator.TAG_ITERATOR, status=status)
            self.mpi_comm.recv(source=status.source, tag=MPIIterator.TAG_ITERATOR)
            try:
                item=self._iter.next()
                self.mpi_comm.send({'type':MPIIterator.NEXT,'value':item},dest=status.source,tag=MPIIterator.TAG_ITERATOR)
            except StopIteration:
                self.mpi_comm.send({'type':MPIIterator.STOP_ITERATION},dest=status.source,tag=MPIIterator.TAG_ITERATOR)
                mpi_stopped+=1
                if mpi_stopped==self.mpi_comm.Get_size()-1:
                    break;
