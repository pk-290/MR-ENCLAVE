import functools
import logging
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mr-enclave.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mr-enclave")

def log_exceptions(func):
    """Decorator to log exceptions for synchronous functions"""
    func.__globals__["logger"] = logger
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        func_name = func.__name__
        try:
            logger.info(f"Starting {func_name}")
            result = func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Completed {func_name} in {execution_time}s")
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error in {func_name} after {execution_time}s: {str(e)}")
            logger.error(f"Error in {func_name} with args={args}, kwargs={kwargs}: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise
    return wrapper

def log_async_exceptions(func):
    """Decorator to log exceptions for async functions"""
    func.__globals__["logger"] = logger
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = datetime.now()
        func_name = func.__name__
        # langfuse = Langfuse()
        try:
            logger.info(f"Starting async {func_name}")
            result = await func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Completed async {func_name} in {execution_time}s")
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error in async {func_name} after {execution_time}s: {str(e)}")
            # logger.error(f"Langfuse trace URL: {langfuse.get_trace_url()} | Trace ID: {langfuse.get_current_trace_id()}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise e
    return wrapper

