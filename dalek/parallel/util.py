import sys
import os
import logging

logger = logging.getLogger(__name__)

def set_engines_cpu_affinity():
    import sys
    if sys.platform.startswith('linux'):
        try:
            import psutil
        except ImportError:
            logger.warning('psutil not available - can not set CPU affinity')
        else:
            from multiprocessing import cpu_count
            p = psutil.Process(os.getpid())
            p.set_cpu_affinity(range(cpu_count()))

