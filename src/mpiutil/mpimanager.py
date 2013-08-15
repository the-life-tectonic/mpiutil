import logging
import cStringIO as StringIO
import sys
from mpi4py import MPI

MPIComm = MPI.COMM_WORLD.Dup()

class MPILogger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET):
        super(MPILogger, self).__init__(name,level)

    def _log(self, level, msg, args, exc_info=None, extra=None):
        if extra==None:
            extra={}
        extra['mpi_rank']=MPIComm.Get_rank()
        extra['mpi_size']=MPIComm.Get_size()
        logging.Logger._log(self,level,msg,args,exc_info,extra)

logging.setLoggerClass(MPILogger)

class  MPIManager(logging.StreamHandler):
    TAG_MGR=4581
    LOG=1
    NEXT_REQUEST=2
    WORKER_DONE=3
    VALUE_AVAILABLE=4
    VALUE_UNAVAILABLE=5

    def __init__(self,items,stream=None,comm=MPIComm,mgr_rank=0):
        self.mgr_rank=mgr_rank
        self.mpi_comm=comm
        self.mpi_rank=comm.Get_rank()
        self.mpi_size=comm.Get_size()
        self.sio=StringIO.StringIO()
        super(MPIManager, self).__init__(self.sio)
        if self.mpi_rank==self.mgr_rank:
            if stream==None:
                stream=sys.stderr
            self._iter=iter(items);
            self._stream=stream

    def emit(self, record):
        # Make the record a string
        logging.StreamHandler.emit(self,record)
        record=self.sio.getvalue()
        self.sio.truncate(0)

        if self.mpi_rank==self.mgr_rank:
            self._write(record)
        else:
            self.mpi_comm.send({'type':MPIManager.LOG,'value':record}, dest=self.mgr_rank, tag=MPIManager.TAG_MGR)

    def _write(self,record):
        self._stream.write(record)
        self._stream.flush()

    def send_done(self):
        print('send_done %d' % self.mpi_rank)
        self.mpi_comm.send({'type':MPIManager.WORKER_DONE}, dest=self.mgr_rank, tag=MPIManager.TAG_MGR)

    def __iter__(self):
        return self

    def next(self):
        if self.mpi_rank==self.mgr_rank:
            raise StopIteration()
        else:
            self.mpi_comm.send({'type':MPIManager.NEXT_REQUEST}, dest=self.mgr_rank, tag=MPIManager.TAG_MGR)
            data = self.mpi_comm.recv(source=self.mgr_rank, tag=MPIManager.TAG_MGR)
            if data['type']==MPIManager.VALUE_UNAVAILABLE:
                raise StopIteration()
            elif data['type']==MPIManager.VALUE_AVAILABLE:
                return data['value']

    def run(self):
        if self.mpi_rank!=self.mgr_rank:
            return False
        mpi_stopped=0
        while mpi_stopped!=self.mpi_comm.Get_size()-1:
            status=MPI.Status()
            data=self.mpi_comm.recv(source=MPI.ANY_SOURCE,tag=MPIManager.TAG_MGR,status=status)

            if data['type']==MPIManager.LOG:
                self._write(data['value'])
            elif data['type']==MPIManager.NEXT_REQUEST:
                try:
                    item=self._iter.next()
                    self.mpi_comm.send({'type':MPIManager.VALUE_AVAILABLE,'value': item},dest=status.Get_source(),tag=MPIManager.TAG_MGR)
                except StopIteration:
                    self.mpi_comm.send({'type':MPIManager.VALUE_UNAVAILABLE},dest=status.Get_source(),tag=MPIManager.TAG_MGR)
            elif data['type']==MPIManager.WORKER_DONE:
                mpi_stopped+=1
        return True
