"""
Adaptive Wait Manager - Dynamic wait time optimization based on server response patterns

This module provides intelligent wait time management that adapts to server response speeds,
ensuring reliability while minimizing unnecessary delays.
"""

import time
import logging
from typing import Optional, List
from collections import deque

logger = logging.getLogger(__name__)


class AdaptiveWaitManager:
    """
    Manages adaptive wait times based on observed server response patterns

    Features:
    - Learns from past response times
    - Adjusts wait times dynamically
    - Provides optimal timeouts for different operations
    """

    def __init__(self, max_history: int = 20):
        """
        Initialize the adaptive wait manager

        Args:
            max_history: Maximum number of response times to track
        """
        self.response_times: deque = deque(maxlen=max_history)
        self.click_times: deque = deque(maxlen=max_history)
        self.submit_times: deque = deque(maxlen=max_history)
        self.page_load_times: deque = deque(maxlen=max_history)

    def record_click_time(self, elapsed: float):
        """Record time taken for a click to be reflected"""
        self.click_times.append(elapsed)
        logger.debug(f"Recorded click time: {elapsed:.3f}s")

    def record_submit_time(self, elapsed: float):
        """Record time taken for form submission"""
        self.submit_times.append(elapsed)
        logger.debug(f"Recorded submit time: {elapsed:.3f}s")

    def record_page_load_time(self, elapsed: float):
        """Record time taken for page load"""
        self.page_load_times.append(elapsed)
        logger.debug(f"Recorded page load time: {elapsed:.3f}s")

    def get_click_timeout(self, default: float = 2.0, max_timeout: float = 5.0) -> float:
        """
        Get optimal timeout for click operations

        Args:
            default: Default timeout if no history
            max_timeout: Maximum timeout to return

        Returns:
            Optimal timeout in seconds
        """
        if not self.click_times:
            return default

        avg = sum(self.click_times) / len(self.click_times)
        # Use 1.5x average, but cap at max_timeout
        optimal = min(avg * 1.5, max_timeout)
        logger.debug(f"Click timeout: {optimal:.3f}s (avg: {avg:.3f}s)")
        return optimal

    def get_submit_timeout(self, default: float = 5.0, max_timeout: float = 10.0) -> float:
        """
        Get optimal timeout for submit operations

        Args:
            default: Default timeout if no history
            max_timeout: Maximum timeout to return

        Returns:
            Optimal timeout in seconds
        """
        if not self.submit_times:
            return default

        avg = sum(self.submit_times) / len(self.submit_times)
        # Use 1.5x average, but cap at max_timeout
        optimal = min(avg * 1.5, max_timeout)
        logger.debug(f"Submit timeout: {optimal:.3f}s (avg: {avg:.3f}s)")
        return optimal

    def get_page_load_timeout(self, default: float = 5.0, max_timeout: float = 10.0) -> float:
        """
        Get optimal timeout for page load operations

        Args:
            default: Default timeout if no history
            max_timeout: Maximum timeout to return

        Returns:
            Optimal timeout in seconds
        """
        if not self.page_load_times:
            return default

        avg = sum(self.page_load_times) / len(self.page_load_times)
        # Use 1.5x average, but cap at max_timeout
        optimal = min(avg * 1.5, max_timeout)
        logger.debug(f"Page load timeout: {optimal:.3f}s (avg: {avg:.3f}s)")
        return optimal

    def get_stats(self) -> dict:
        """Get statistics about recorded times"""
        stats = {
            'click': self._calculate_stats(self.click_times),
            'submit': self._calculate_stats(self.submit_times),
            'page_load': self._calculate_stats(self.page_load_times)
        }
        return stats

    def _calculate_stats(self, times: deque) -> dict:
        """Calculate statistics for a set of times"""
        if not times:
            return {'count': 0, 'avg': 0, 'min': 0, 'max': 0}

        times_list = list(times)
        return {
            'count': len(times_list),
            'avg': sum(times_list) / len(times_list),
            'min': min(times_list),
            'max': max(times_list)
        }

    def reset(self):
        """Reset all recorded times"""
        self.response_times.clear()
        self.click_times.clear()
        self.submit_times.clear()
        self.page_load_times.clear()
        logger.info("Adaptive wait manager reset")


class TimedOperation:
    """Context manager for timing operations and recording to AdaptiveWaitManager"""

    def __init__(self, wait_manager: AdaptiveWaitManager, operation_type: str):
        """
        Initialize timed operation

        Args:
            wait_manager: The adaptive wait manager to record to
            operation_type: Type of operation ('click', 'submit', 'page_load')
        """
        self.wait_manager = wait_manager
        self.operation_type = operation_type
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time and exc_type is None:  # Only record successful operations
            elapsed = time.time() - self.start_time

            if self.operation_type == 'click':
                self.wait_manager.record_click_time(elapsed)
            elif self.operation_type == 'submit':
                self.wait_manager.record_submit_time(elapsed)
            elif self.operation_type == 'page_load':
                self.wait_manager.record_page_load_time(elapsed)
