import atexit
import logging
import threading
import cStringIO as StringIO
import sys
from mpi4py import MPI

class MPILogger(logging.Logger):
    _comm=MPI.COMM_WORLD
    def __init__(self, name, level=logging.NOTSET):
        super(MPILogger, self).__init__(name,level)

    def _log(self, level, msg, args, exc_info=None, extra=None):
        if extra==None:
            extra={}
        extra['mpi_rank']=MPILogger._comm.Get_rank()
        extra['mpi_size']=MPILogger._comm.Get_size()
        logging.Logger._log(self,level,msg,args,exc_info,extra)

class  MPIHandler(logging.StreamHandler):
    TAG_LOG=4581
    LOG=0
    DONE=1

    def __init__(self,stream=None,comm=MPI.COMM_WORLD,logger_rank=0):
        self.logger_rank=logger_rank
        self.mpi_comm=comm
        self.mpi_rank=comm.Get_rank()
        self.mpi_size=comm.Get_size()
        self.sio=StringIO.StringIO()
        super(MPIHandler, self).__init__(self.sio)
        if self.mpi_rank==self.logger_rank:
            if stream==None:
                stream=sys.stderr
            self._stream=stream
            self._thread=threading.Thread(target=self.run)
            atexit.register(self._thread.join)
            self._thread.start()
        else:
            atexit.register(self.send_done)

    def emit(self, record):
        logging.StreamHandler.emit(self,record)
        record=self.sio.getvalue()
        self.sio.trucate(0)
        if self.mpi_rank==self.logger_rank:
            self._write(record)
        else:
            self.mpi_comm.send({'type':MPIHandler.LOG,'value':record},dest=self.logger_rank,tag=MPIHandler.TAG_LOG)

    def _write(self,record):
        self.stream.write(record)
        self.stream.flush()

    def send_done(self):
        self.mpi_comm.send({'type':MPIHandler.DONE},dest=self.logger_rank,tag=MPIHandler.TAG_LOG)

    def run(self):
        mpi_stopped=0
        while True:
            status=MPI.Status()
            data=self.mpi_comm.recv(source=MPI.ANY_SOURCE, tag=MPIHandler.TAG_LOG,status=status)
            if data['type']==MPIHandler.LOG:
                self._write(data['value'])
            elif data['type']==MPIHandler.DONE:
                mpi_stopped+=1
                if mpi_stopped==self.mpi_comm.Get_size()-1:
                    break;

