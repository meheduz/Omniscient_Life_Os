"""
Performance monitoring and logging utilities
"""
import time
import functools
from typing import Callable, Any

class PerformanceMonitor:
    """Simple performance monitoring for key operations"""
    
    def __init__(self):
        self.metrics = {}
    
    def record(self, operation: str, duration: float):
        """Record operation duration"""
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(duration)
    
    def get_stats(self, operation: str) -> dict:
        """Get statistics for an operation"""
        if operation not in self.metrics or not self.metrics[operation]:
            return {}
        
        durations = self.metrics[operation]
        return {
            "count": len(durations),
            "avg": sum(durations) / len(durations),
            "min": min(durations),
            "max": max(durations),
        }
    
    def print_summary(self):
        """Print performance summary"""
        print("\n=== Performance Summary ===")
        for op, durations in self.metrics.items():
            stats = self.get_stats(op)
            print(f"{op}: {stats['count']} calls, avg={stats['avg']:.3f}s, min={stats['min']:.3f}s, max={stats['max']:.3f}s")

# Global monitor instance
monitor = PerformanceMonitor()

def timed(operation_name: str):
    """Decorator to time function execution"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start
            monitor.record(operation_name, duration)
            return result
        return wrapper
    return decorator

async def timed_async(operation_name: str):
    """Decorator to time async function execution"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start = time.time()
            result = await func(*args, **kwargs)
            duration = time.time() - start
            monitor.record(operation_name, duration)
            return result
        return wrapper
    return decorator
