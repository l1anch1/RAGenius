"""
Timing Monitor
全链路时间监控装饰器

支持同步/异步函数计时，支持嵌套调用层级显示
"""
import time
import asyncio
import functools
import logging
import threading
from typing import Any, Callable, Optional
from contextlib import contextmanager
from dataclasses import dataclass, field
from collections import defaultdict

from config import TIMING_ENABLED as _CONFIG_TIMING_ENABLED
from config import TIMING_SHOW_IN_TERMINAL as _CONFIG_TIMING_SHOW_IN_TERMINAL
from config import TIMING_MIN_DURATION_MS as _CONFIG_TIMING_MIN_DURATION_MS

logger = logging.getLogger(__name__)


# ANSI 颜色代码
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


@dataclass
class TimingStats:
    """单次计时统计"""
    name: str
    duration_ms: float
    level: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class PipelineTimingContext:
    """流水线计时上下文（线程安全）"""
    enabled: bool = True
    show_in_terminal: bool = True
    level: int = 0
    stages: list = field(default_factory=list)
    start_time: float = 0.0
    
    def reset(self):
        self.level = 0
        self.stages = []
        self.start_time = time.perf_counter()


# 线程局部存储，支持多线程环境
_thread_local = threading.local()


def get_timing_context() -> PipelineTimingContext:
    """获取当前线程的计时上下文"""
    if not hasattr(_thread_local, 'context'):
        _thread_local.context = PipelineTimingContext()
    return _thread_local.context


def reset_timing_context():
    """重置当前线程的计时上下文"""
    ctx = get_timing_context()
    ctx.reset()


# 全局配置（从 config.py 读取，支持运行时覆盖）
TIMING_ENABLED = _CONFIG_TIMING_ENABLED
TIMING_SHOW_IN_TERMINAL = _CONFIG_TIMING_SHOW_IN_TERMINAL
TIMING_MIN_DURATION_MS = _CONFIG_TIMING_MIN_DURATION_MS


def set_timing_enabled(enabled: bool):
    """全局启用/禁用计时"""
    global TIMING_ENABLED
    TIMING_ENABLED = enabled


def set_timing_terminal_output(enabled: bool):
    """全局启用/禁用终端输出"""
    global TIMING_SHOW_IN_TERMINAL
    TIMING_SHOW_IN_TERMINAL = enabled


def _format_duration(ms: float) -> str:
    """格式化时间显示"""
    if ms < 1:
        return f"{ms*1000:.1f}μs"
    elif ms < 1000:
        return f"{ms:.1f}ms"
    else:
        return f"{ms/1000:.2f}s"


def _get_color_by_duration(ms: float) -> str:
    """根据耗时返回颜色"""
    if ms < 10:
        return Colors.GREEN
    elif ms < 100:
        return Colors.CYAN
    elif ms < 1000:
        return Colors.YELLOW
    else:
        return Colors.RED


def _print_timing(name: str, duration_ms: float, level: int = 0, metadata: dict = None):
    """打印计时信息到终端"""
    if not TIMING_SHOW_IN_TERMINAL:
        return
    
    if duration_ms < TIMING_MIN_DURATION_MS:
        return
    
    indent = "  " * level
    color = _get_color_by_duration(duration_ms)
    duration_str = _format_duration(duration_ms)
    
    # 构建输出行
    prefix = f"{Colors.DIM}│{Colors.RESET}" if level > 0 else ""
    marker = "├─" if level > 0 else "▶"
    
    line = f"{prefix}{indent}{Colors.BOLD}{marker}{Colors.RESET} {name}: {color}{duration_str}{Colors.RESET}"
    
    # 添加元数据
    if metadata:
        meta_parts = []
        for key, value in metadata.items():
            if isinstance(value, float):
                meta_parts.append(f"{key}={value:.2f}")
            elif isinstance(value, (list, tuple)):
                meta_parts.append(f"{key}={len(value)}")
            else:
                meta_parts.append(f"{key}={value}")
        if meta_parts:
            line += f" {Colors.DIM}({', '.join(meta_parts)}){Colors.RESET}"
    
    print(line)


def timed(
    name: Optional[str] = None,
    log_args: bool = False,
    metadata_keys: list = None
):
    """
    计时装饰器 - 支持同步和异步函数
    
    Args:
        name: 显示名称（默认使用函数名）
        log_args: 是否记录函数参数
        metadata_keys: 从返回值中提取的元数据键（用于返回dict的函数）
    
    Usage:
        @timed("查询扩展")
        def expand_query(query: str) -> List[str]:
            ...
        
        @timed("LLM生成", metadata_keys=["tokens"])
        async def generate_answer(query: str) -> dict:
            ...
    """
    def decorator(func: Callable) -> Callable:
        display_name = name or func.__name__
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            if not TIMING_ENABLED:
                return func(*args, **kwargs)
            
            ctx = get_timing_context()
            current_level = ctx.level
            ctx.level += 1
            
            start_time = time.perf_counter()
            result = None
            error = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                
                # 构建元数据
                metadata = {}
                if log_args and args:
                    # 跳过 self 参数
                    arg_start = 1 if hasattr(func, '__self__') or (args and hasattr(args[0], '__class__')) else 0
                    if len(args) > arg_start:
                        first_arg = args[arg_start]
                        if isinstance(first_arg, str) and len(first_arg) < 50:
                            metadata["query"] = first_arg[:30] + "..." if len(first_arg) > 30 else first_arg
                
                if metadata_keys and isinstance(result, dict):
                    for key in metadata_keys:
                        if key in result:
                            metadata[key] = result[key]
                
                if error:
                    metadata["error"] = str(error)[:50]
                
                # 记录统计
                stat = TimingStats(
                    name=display_name,
                    duration_ms=duration_ms,
                    level=current_level,
                    metadata=metadata
                )
                ctx.stages.append(stat)
                
                # 打印到终端
                _print_timing(display_name, duration_ms, current_level, metadata)
                
                ctx.level -= 1
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            if not TIMING_ENABLED:
                return await func(*args, **kwargs)
            
            ctx = get_timing_context()
            current_level = ctx.level
            ctx.level += 1
            
            start_time = time.perf_counter()
            result = None
            error = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                
                # 构建元数据
                metadata = {}
                if log_args and args:
                    arg_start = 1 if hasattr(func, '__self__') or (args and hasattr(args[0], '__class__')) else 0
                    if len(args) > arg_start:
                        first_arg = args[arg_start]
                        if isinstance(first_arg, str) and len(first_arg) < 50:
                            metadata["query"] = first_arg[:30] + "..." if len(first_arg) > 30 else first_arg
                
                if metadata_keys and isinstance(result, dict):
                    for key in metadata_keys:
                        if key in result:
                            metadata[key] = result[key]
                
                if error:
                    metadata["error"] = str(error)[:50]
                
                stat = TimingStats(
                    name=display_name,
                    duration_ms=duration_ms,
                    level=current_level,
                    metadata=metadata
                )
                ctx.stages.append(stat)
                
                _print_timing(display_name, duration_ms, current_level, metadata)
                
                ctx.level -= 1
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


@contextmanager
def timing_scope(name: str, metadata: dict = None):
    """
    计时上下文管理器 - 用于代码块计时
    
    Usage:
        with timing_scope("检索流程"):
            results = retriever.retrieve(query)
    """
    if not TIMING_ENABLED:
        yield
        return
    
    ctx = get_timing_context()
    current_level = ctx.level
    ctx.level += 1
    
    start_time = time.perf_counter()
    
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        stat = TimingStats(
            name=name,
            duration_ms=duration_ms,
            level=current_level,
            metadata=metadata or {}
        )
        ctx.stages.append(stat)
        
        _print_timing(name, duration_ms, current_level, metadata)
        
        ctx.level -= 1


def pipeline_start(name: str = "Pipeline"):
    """
    标记流水线开始，打印开始标题
    
    Usage:
        pipeline_start("RAG 检索流水线")
        # ... 执行各阶段 ...
        pipeline_end()
    """
    if not TIMING_ENABLED or not TIMING_SHOW_IN_TERMINAL:
        return
    
    reset_timing_context()
    
    print()
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.HEADER}⏱  {name} Started{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.RESET}")


def pipeline_end(name: str = "Pipeline"):
    """
    标记流水线结束，打印汇总统计
    """
    if not TIMING_ENABLED or not TIMING_SHOW_IN_TERMINAL:
        return
    
    ctx = get_timing_context()
    total_ms = (time.perf_counter() - ctx.start_time) * 1000 if ctx.start_time > 0 else 0
    
    print(f"{Colors.BOLD}{Colors.HEADER}{'─'*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}✓ {name} Done - Total: {_format_duration(total_ms)}{Colors.RESET}")
    
    # 打印各阶段统计
    if ctx.stages:
        top_stages = sorted(
            [s for s in ctx.stages if s.level == 0],
            key=lambda x: x.duration_ms,
            reverse=True
        )[:5]
        
        if top_stages:
            print(f"{Colors.DIM}Top time-consuming stages:{Colors.RESET}")
            for stage in top_stages:
                pct = (stage.duration_ms / total_ms * 100) if total_ms > 0 else 0
                color = _get_color_by_duration(stage.duration_ms)
                print(f"  {stage.name}: {color}{_format_duration(stage.duration_ms)}{Colors.RESET} ({pct:.1f}%)")
    
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.RESET}")
    print()


def get_timing_summary() -> dict:
    """获取计时统计摘要"""
    ctx = get_timing_context()
    total_ms = (time.perf_counter() - ctx.start_time) * 1000 if ctx.start_time > 0 else 0
    
    stages_summary = []
    for stage in ctx.stages:
        stages_summary.append({
            "name": stage.name,
            "duration_ms": stage.duration_ms,
            "level": stage.level,
            "metadata": stage.metadata
        })
    
    return {
        "total_duration_ms": total_ms,
        "stages": stages_summary,
        "stage_count": len(ctx.stages)
    }

