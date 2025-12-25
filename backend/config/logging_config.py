"""
Logging Configuration
日志配置模块

集中管理日志格式和过滤规则，提供美观的终端输出。
"""
import logging


# =============================================================================
# ANSI 颜色和样式
# =============================================================================

class Style:
    """终端样式常量"""
    # 颜色
    CYAN = '\033[36m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[91m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    GRAY = '\033[90m'
    WHITE = '\033[97m'
    
    # 样式
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'
    
    # 组合样式
    HEADER = f'{BOLD}{CYAN}'
    SUBHEADER = f'{BOLD}{WHITE}'
    SUCCESS = f'{GREEN}'
    WARNING = f'{YELLOW}'
    ERROR = f'{RED}'
    MUTED = f'{DIM}'


# =============================================================================
# 美化输出函数
# =============================================================================

def print_stage_header(stage_name: str, icon: str = "▸"):
    """打印阶段标题"""
    print(f"\n{Style.HEADER}{icon} {stage_name}{Style.RESET}")
    print(f"{Style.GRAY}{'─' * 50}{Style.RESET}")


def print_stage_result(label: str, value: str, indent: int = 0):
    """打印阶段结果"""
    spaces = "  " * indent
    print(f"{spaces}{Style.MUTED}│{Style.RESET} {label}: {Style.WHITE}{value}{Style.RESET}")


def print_document(index: int, score: float, source: str, preview: str, indent: int = 1):
    """打印文档条目"""
    spaces = "  " * indent
    # 分数颜色：高分绿色，低分黄色
    score_color = Style.GREEN if score > 0 else Style.YELLOW
    print(f"{spaces}{Style.MUTED}│{Style.RESET} {Style.BOLD}{index}.{Style.RESET} "
          f"[{score_color}{score:.4f}{Style.RESET}] "
          f"{Style.CYAN}{source}{Style.RESET}")
    print(f"{spaces}{Style.MUTED}│    {preview}...{Style.RESET}")


def print_document_compact(index: int, score: float, source: str, preview: str, indent: int = 1):
    """打印紧凑格式文档（单行）"""
    spaces = "  " * indent
    score_color = Style.GREEN if score > 0 else Style.YELLOW
    # 截断预览文本
    short_preview = preview[:80] + "..." if len(preview) > 80 else preview
    print(f"{spaces}{Style.MUTED}│{Style.RESET} {index}. "
          f"[{score_color}{score:.4f}{Style.RESET}] "
          f"{Style.CYAN}{source}{Style.RESET}: {Style.DIM}{short_preview}{Style.RESET}")


def print_query_list(queries: list, indent: int = 1):
    """打印查询列表"""
    spaces = "  " * indent
    for i, q in enumerate(queries, 1):
        print(f"{spaces}{Style.MUTED}│{Style.RESET} {i}. {q}")


def print_summary(label: str, count: int, extra: str = ""):
    """打印汇总信息"""
    extra_str = f" {Style.DIM}({extra}){Style.RESET}" if extra else ""
    print(f"{Style.MUTED}│{Style.RESET} {label}: {Style.BOLD}{count}{Style.RESET}{extra_str}")


def print_more(remaining: int):
    """打印省略提示"""
    print(f"{Style.MUTED}│  ... and {remaining} more{Style.RESET}")


# =============================================================================
# 日志格式器
# =============================================================================

class CleanFormatter(logging.Formatter):
    """
    简洁日志格式器
    
    根据消息内容智能格式化，支持特殊标记。
    """
    
    def format(self, record):
        msg = record.getMessage()
        
        # ERROR 级别 - 红色醒目
        if record.levelno >= logging.ERROR:
            return f"{Style.ERROR}✗ ERROR: {msg}{Style.RESET}"
        
        # WARNING 级别 - 黄色警告
        if record.levelno >= logging.WARNING:
            return f"{Style.WARNING}⚠ {msg}{Style.RESET}"
        
        # INFO 级别 - 根据内容智能格式化
        
        # 分隔线
        if msg.startswith('─') or msg.startswith('═'):
            return f"{Style.MUTED}{msg}{Style.RESET}"
        
        # 阶段标题 [StageName]
        if msg.startswith('[') and ']' in msg:
            stage_end = msg.index(']')
            stage_name = msg[1:stage_end]
            content = msg[stage_end + 1:].strip()
            return f"{Style.MUTED}│{Style.RESET} {Style.CYAN}{Style.BOLD}[{stage_name}]{Style.RESET} {content}"
        
        # 文档条目（带 📄 图标）
        if '📄' in msg:
            return f"{Style.MUTED}│{Style.RESET}{msg}"
        
        # 带箭头的查询列表
        if '→' in msg:
            return f"{Style.MUTED}│{Style.RESET} {msg}"
        
        # 数字列表项（深度缩进）
        stripped = msg.lstrip()
        indent = len(msg) - len(stripped)
        if stripped and stripped[0].isdigit() and '.' in stripped[:3]:
            spaces = ' ' * indent
            return f"{Style.MUTED}│{spaces}{Style.RESET}{stripped}"
        
        # 深度缩进内容（文档预览）
        if indent >= 4:
            spaces = ' ' * indent
            return f"{Style.MUTED}│{spaces}{stripped}{Style.RESET}"
        
        # 普通缩进
        if msg.startswith('  '):
            return f"{Style.MUTED}│{Style.RESET}{msg}"
        
        # 普通消息
        return f"{Style.MUTED}│{Style.RESET} {msg}"


# =============================================================================
# 第三方库过滤
# =============================================================================

THIRD_PARTY_LIBS = [
    # Web 框架
    "werkzeug",
    # HTTP 客户端
    "httpx", "urllib3", "httpcore", "requests", "aiohttp",
    # AI/ML 库
    "openai", "sentence_transformers", "torch", "transformers",
    # HuggingFace
    "huggingface_hub", "datasets", "filelock", "fsspec",
    # LangChain
    "langchain", "langchain_core", "langchain_community",
    "langchain_openai", "langchain_ollama", "langchain_huggingface",
    "langchain_chroma", "langchain_text_splitters",
    # 向量数据库
    "chromadb",
    # 其他
    "tqdm", "chardet", "charset_normalizer",
]


def setup_logging():
    """
    配置全局日志
    
    - 项目代码：显示所有 INFO 及以上级别
    - 第三方库：只显示 ERROR 级别
    """
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(CleanFormatter())
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [console_handler]
    
    for lib in THIRD_PARTY_LIBS:
        logging.getLogger(lib).setLevel(logging.ERROR)

