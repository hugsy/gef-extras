from typing import (Callable, Dict, Iterator, List, Optional, Tuple, Union,
                    overload)

PYTHONDIR: str


def execute(command, from_tty=False, to_string=False) -> None: ...
def breakpoints() -> List[Breakpoint]: ...
def rbreak(regex, minsyms=False, throttle=None,
           symtabs: List[Symtab] = []) -> List[Breakpoint]: ...


def parameter(parameter: str): ...
def history(number: int) -> Value: ...
def convenience_variable(name: str) -> Union[None, Value]: ...
def set_convenience_variable(name: str, value) -> None: ...
def parse_and_eval(expression: str) -> Value: ...
def find_pc_line(pc) -> Symtab_and_line: ...
def post_event(event: Callable) -> None: ...


GdbStream = int

STDOUT: GdbStream
STDERR: GdbStream
STDLOG: GdbStream


def write(string: str, stream: GdbStream = ...): ...
def flush(stream: GdbStream = ...): ...
def target_charset() -> str: ...
def target_wide_charset() -> str: ...
def solib_name(address: int) -> str: ...
def decode_line(expression: Optional[str] = None) -> Tuple[str,
                                                           Union[None, List[Symtab_and_line]]]: ...


def prompt_hook(current_prompt: Callable[[Callable], str]) -> str: ...


class error(RuntimeError):
    ...


class MemoryError(error):
    ...


class GdbError(Exception):
    ...


class Value:
    address: Optional[Value]
    is_optimized_out: bool
    type: Type
    is_lazy: bool
    def __init__(self, value, type: Optional[Type] = None): ...

    def cast(self, type: Type) -> Value: ...
    def defererence(self) -> Value: ...
    def referenced_value(self) -> Value: ...
    def reference_value(self) -> Value: ...
    def const_value(self) -> Value: ...
    def dynamic_cast(self, type: Type) -> Value: ...
    def reinterpret_cast(self, type: Type) -> Value: ...
    def format_string(self, *args) -> str: ...

    def string(self, encoding: Optional[str] = None, errors=None,
               length: Optional[int] = None) -> str: ...

    def lazy_string(
        self, encoding: Optional[str] = None, length: Optional[int] = None) -> str: ...

    def fetch_lazy(self) -> None: ...

    def __abs__(self) -> int: ...


def lookup_type(name, block: Optional[Block] = None) -> Type: ...


class Type:
    alignof: int
    code: TypeCode
    name: Optional[str]
    sizeof: int
    tag: Optional[str]
    objfile: Optional[Objfile]
    def fields(self) -> List[Field]: ...
    def array(self, n1: int, n2: Optional[int] = None) -> Type: ...
    def vector(self, n1: int, n2: Optional[int] = None) -> Type: ...
    def const(self) -> Type: ...
    def volatile(self) -> Type: ...
    def unqualified(self) -> Type: ...
    def range(self) -> Tuple[Type, Type]: ...
    def reference(self) -> Type: ...
    def pointer(self) -> Type: ...
    def strip_typedefs(self) -> Type: ...
    def target(self) -> Type: ...
    def template_argument(
        self, n: int, block: Optional[Block] = None) -> Union[Value, Type]: ...

    def optimized_out(self) -> Value: ...


class Field:
    bitpos: int
    enumval: Optional[int]
    name: Optional[str]
    artificial: bool
    is_base_class: bool
    bitsize: int
    type: Optional[Type]
    parent_type: Optional[Type]


TypeCode = int

TYPE_CODE_PTR: TypeCode
TYPE_CODE_ARRAY: TypeCode
TYPE_CODE_STRUCT: TypeCode
TYPE_CODE_UNION: TypeCode
TYPE_CODE_ENUM: TypeCode
TYPE_CODE_FLAGS: TypeCode
TYPE_CODE_FUNC: TypeCode
TYPE_CODE_INT: TypeCode
TYPE_CODE_FLT: TypeCode
TYPE_CODE_VOID: TypeCode
TYPE_CODE_SET: TypeCode
TYPE_CODE_RANGE: TypeCode
TYPE_CODE_STRING: TypeCode
TYPE_CODE_BITSTRING: TypeCode
TYPE_CODE_ERROR: TypeCode
TYPE_CODE_METHOD: TypeCode
TYPE_CODE_METHODPTR: TypeCode
TYPE_CODE_MEMBERPTR: TypeCode
TYPE_CODE_REF: TypeCode
TYPE_CODE_RVALUE_REF: TypeCode
TYPE_CODE_CHAR: TypeCode
TYPE_CODE_BOOL: TypeCode
TYPE_CODE_COMPLEX: TypeCode
TYPE_CODE_TYPEDEF: TypeCode
TYPE_CODE_NAMESPACE: TypeCode
TYPE_CODE_DECFLOAT: TypeCode
TYPE_CODE_INTERNAL_FUNCTION: TypeCode


def default_visualizer(value: Value): ...


pretty_printers: List


class FrameFilter:
    def filter(self, iterator: Iterator): ...
    name: str
    enabled: bool
    priority: int


def inferiors() -> List[Inferior]: ...
def selected_inferior() -> Inferior: ...


class Inferior:
    num: ...
    pid: int
    was_attached: bool
    progspace: Progspace
    def is_valid(self) -> bool: ...
    def threads(self) -> List[InferiorThread]: ...
    def architecture(self) -> Architecture: ...
    def read_memory(self, address: int, length: int) -> memoryview: ...

    def write_memory(self, address: int,
                     buffer: Union[str, bytes], length: int) -> None: ...
    def search_memory(self, address: int, length: int,
                      pattern: Union[str, bytes]) -> int: ...

    def thread_from_handle(self, handle) -> InferiorThread: ...


class Event(dict):
    ...


class ThreadEvent:
    inferior_thread: Optional[InferiorThread]


class ContinueEvent(ThreadEvent):
    ...


class ExitedEvent:
    exit_code: Optional[int]
    inferior: Inferior


class StopEvent(ThreadEvent):
    pass


class SignalEvent(StopEvent):
    stop_signal: str


class BreakpointEvent(SignalEvent):
    breakpoints: List[Breakpoint]
    breakpoint: Breakpoint


class ClearObjFilesEvent:
    progspace: Progspace


class InferiorCallPreEvent:
    tpid: int
    address: int


class InferiorCallPostEvent:
    tpid: int
    address: int


class MemoryChangedEvent:
    address: int
    lenth: int


class RegisterChangedEvent:
    frame: Frame
    regnum: int


class NewInferiorEvent:
    inferior: Inferior


class InferiorDeletedEvent:
    inferior: Inferior


class NewThreadEvent(ThreadEvent):
    inferior_thread: InferiorThread


class NewObjFileEvent:
    new_objfile: Objfile


class EventRegistry:
    def connect(self, object) -> None: ...
    def disconnect(self, object) -> None: ...


class __events:
    class __cont(EventRegistry):
        def connect(self, object: Callable[[ContinueEvent], None]) -> None: ...
        def disconnect(
            self, object: Callable[[ContinueEvent], None]) -> None: ...
    cont: __cont

    class __exited(EventRegistry):
        def connect(self, object: Callable[[ExitedEvent], None]) -> None: ...
        def disconnect(
            self, object: Callable[[ExitedEvent], None]) -> None: ...
    exited: __exited

    class __stop(EventRegistry):
        def connect(self, object: Callable[[
                    Union[SignalEvent, BreakpointEvent]], None]) -> None: ...
        def disconnect(self, object: Callable[[
                       Union[SignalEvent, BreakpointEvent]], None]) -> None: ...
    stop: __stop

    class __new_objfile(EventRegistry):
        def connect(
            self, object: Callable[[NewObjFileEvent], None]) -> None: ...
        def disconnect(
            self, object: Callable[[NewObjFileEvent], None]) -> None: ...
    new_objfile: __new_objfile

    class __clear_objfiles(EventRegistry):
        def connect(
            self, object: Callable[[ClearObjFilesEvent], None]) -> None: ...
        def disconnect(
            self, object: Callable[[ClearObjFilesEvent], None]) -> None: ...
    clear_objfiles: __clear_objfiles

    class __inferior_call(EventRegistry):
        def connect(self, object: Callable[[
                    Union[InferiorCallPreEvent, InferiorCallPostEvent]], None]) -> None: ...
        def disconnect(self, object: Callable[[
                       Union[InferiorCallPreEvent, InferiorCallPostEvent]], None]) -> None: ...
    inferior_call: __inferior_call

    class __memory_changed(EventRegistry):
        def connect(
            self, object: Callable[[MemoryChangedEvent], None]) -> None: ...
        def disconnect(
            self, object: Callable[[MemoryChangedEvent], None]) -> None: ...
    memory_changed: __memory_changed

    class __breakpoint(EventRegistry):
        def connect(self, object: Callable[[Breakpoint], None]) -> None: ...
        def disconnect(self, object: Callable[[Breakpoint], None]) -> None: ...
    breakpoint_created: __breakpoint
    breakpoint_modified: __breakpoint
    breakpoint_deleted: __breakpoint

    class __before_prompt(EventRegistry):
        def connect(self, object: Callable[[], None]) -> None: ...
        def disconnect(self, object: Callable[[], None]) -> None: ...
    before_prompt: __before_prompt

    class __new_inferior(EventRegistry):
        def connect(
            self, object: Callable[[NewInferiorEvent], None]) -> None: ...
        def disconnect(
            self, object: Callable[[NewInferiorEvent], None]) -> None: ...
    new_inferior: __new_inferior

    class __inferior_deleted(EventRegistry):
        def connect(
            self, object: Callable[[InferiorDeletedEvent], None]) -> None: ...
        def disconnect(
            self, object: Callable[[InferiorDeletedEvent], None]) -> None: ...
    inferior_deleted: __inferior_deleted

    class __new_thread(EventRegistry):
        def connect(
            self, object: Callable[[NewThreadEvent], None]) -> None: ...
        def disconnect(
            self, object: Callable[[NewThreadEvent], None]) -> None: ...
    new_thread: __new_thread


events: __events


def selected_thread() -> InferiorThread: ...


class InferiorThread:
    name: Optional[str]
    num: int
    global_num: int
    ptid: int
    inferior: Inferior
    def is_valid(self) -> bool: ...
    def switch(self) -> None: ...
    def is_stopped(self) -> bool: ...
    def is_running(self) -> bool: ...
    def is_exited(self) -> bool: ...
    def handle(self) -> bytes: ...


def start_recording(
    method: Optional[str] = None, format: Optional[str] = None) -> Record: ...


def current_recording() -> Optional[Record]: ...
def stop_recording() -> None: ...


class Record:
    method: str
    format: str
    begin: Instruction
    end: Instruction
    replay_position: Optional[Instruction]
    instruction_history: List[Instruction]
    function_call_history: List[RecordFunctionSegment]
    def goto(self, instruction: Instruction) -> None: ...


class Instruction:
    pc: int
    data: memoryview
    decoded: str
    size: int


class RecordInstruction(Instruction):
    number: int
    sal: Symtab_and_line
    is_speculative: bool


class RecordGap:
    number: int
    error_code: int
    error_string: str


class RecordFunctionSegment:
    number: int
    symbol: Symbol
    level: Optional[int]
    instructions: List[Union[RecordInstruction, RecordGap]]
    up: Optional[RecordFunctionSegment]
    prev: Optional[RecordFunctionSegment]
    next: Optional[RecordFunctionSegment]


class Command:
    def __init__(self, name: str, command_class: Optional[CommandClass] = None,
                 completer_class: Optional[CompleteClass] = None, prefix: Optional[bool] = None): ...

    def dont_repeat(self) -> None: ...
    def invoke(self, argument: str, from_tty: bool): ...
    def complete(self, text: str, word: str): ...


CommandClass = int

COMMAND_NONE: CommandClass
COMMAND_RUNNING: CommandClass
COMMAND_DATA: CommandClass
COMMAND_STACK: CommandClass
COMMAND_FILES: CommandClass
COMMAND_SUPPORT: CommandClass
COMMAND_STATUS: CommandClass
COMMAND_BREAKPOINTS: CommandClass
COMMAND_TRACEPOINTS: CommandClass
COMMAND_USER: CommandClass
COMMAND_OBSCURE: CommandClass
COMMAND_MAINTENANCE: CommandClass


CompleteClass = int

COMPLETE_NONE: CompleteClass
COMPLETE_FILENAME: CompleteClass
COMPLETE_LOCATION: CompleteClass
COMPLETE_COMMAND: CompleteClass
COMPLETE_SYMBOL: CompleteClass
COMPLETE_EXPRESSION: CompleteClass


class Parameter:
    def __init__(self, name: str, command_class: CommandClass,
                 parameter_class: __parameter_class, enum_sequence: Optional[List[str]] = None): ...
    set_doc: str
    show_doc: str
    value: ...

    def get_set_string(self) -> None: ...
    def get_show_string(self, svalue: str) -> None: ...


class __parameter_class:
    pass


PARAM_BOOLEAN: __parameter_class
PARAM_AUTO_BOOLEAN: __parameter_class
PARAM_UINTEGER: __parameter_class
PARAM_INTEGER: __parameter_class
PARAM_STRING: __parameter_class
PARAM_STRING_NOESCAPE: __parameter_class
PARAM_OPTIONAL_FILENAME: __parameter_class
PARAM_FILENAME: __parameter_class
PARAM_ZINTEGER: __parameter_class
PARAM_ZUINTEGER: __parameter_class
PARAM_ZUINTEGER_UNLIMITED: __parameter_class
PARAM_ENUM: __parameter_class


class Function:
    def __init__(self, name: str): ...
    def invoke(self, *args): ...


def current_progspace() -> Progspace: ...
def progspaces() -> List[Progspace]: ...


class Progspace:
    filename: str
    pretty_printers: list
    type_printers: list
    frame_filters: Dict[str, FrameFilter]
    def block_for_pc(self, pc: int) -> Optional[Block]: ...
    def find_pc_line(self, pc: int) -> Optional[Symtab_and_line]: ...
    def is_valid(self) -> bool: ...
    def objfiles(self) -> List[Objfile]: ...
    def solid_name(self, address: int) -> str: ...


def current_objfile() -> Objfile: ...
def objfiles() -> List[Objfile]: ...


def lookup_objfile(name: Union[str, int],
                   by_build_id: Optional[bool] = None) -> Objfile: ...


class Objfile:
    filename: Optional[str]
    username: Optional[str]
    owner: Optional[Objfile]
    build_id: Optional[str]
    progspace: Progspace
    pretty_printers: list
    type_printers: list
    frame_filters: List[FrameFilter]
    def is_valid(self) -> bool: ...
    def add_separate_debug_file(self, file: str) -> None: ...

    def lookup_global_symbol(
        self, name: str, domain: Optional[str] = None) -> Optional[Symbol]: ...
    def lookup_static_symbol(
        self, name: str, domain: Optional[str] = None) -> Optional[Symbol]: ...


def selected_frame() -> Frame: ...
def newest_frame() -> Frame: ...
def invalidate_cached_frames() -> None: ...


class Frame:
    def is_valid(self) -> bool: ...
    def name(self) -> str: ...
    def architecture(self) -> Architecture: ...
    def type(self) -> FrameType: ...
    def unwind_stop_reason(self) -> FrameUnwindStopReason: ...
    def pc(self) -> int: ...
    def block(self) -> Block: ...
    def function(self) -> Symbol: ...
    def older(self) -> Frame: ...
    def newer(self) -> Frame: ...
    def find_sal(self) -> Symtab_and_line: ...
    def read_register(self, register: str) -> Value: ...
    def read_var(self, variable: Union[Symbol, str],
                 block: Optional[Block] = None) -> Symbol: ...

    def select(self) -> None: ...


FrameType = int

NORMAL_FRAME: FrameType
DUMMY_FRAME: FrameType
INLINE_FRAME: FrameType
TAILCALL_FRAME: FrameType
SIGTRAMP_FRAME: FrameType
ARCH_FRAME: FrameType
SENTINEL_FRAME: FrameType


FrameUnwindStopReason = int

FRAME_UNWIND_NO_REASON: FrameUnwindStopReason
FRAME_UNWIND_NULL_ID: FrameUnwindStopReason
FRAME_UNWIND_OUTERMOST: FrameUnwindStopReason
FRAME_UNWIND_UNAVAILABLE: FrameUnwindStopReason
FRAME_UNWIND_INNER_ID: FrameUnwindStopReason
FRAME_UNWIND_SAME_ID: FrameUnwindStopReason
FRAME_UNWIND_NO_SAVED_PC: FrameUnwindStopReason
FRAME_UNWIND_MEMORY_ERROR: FrameUnwindStopReason
FRAME_UNWIND_FIRST_ERROR: FrameUnwindStopReason


def frame_stop_reason_string(reason: FrameUnwindStopReason) -> str: ...


def block_for_pc(pc: int) -> Block: ...


class Block:
    def is_valid(self) -> bool: ...
    def __getitem__(self, idx: int) -> Symbol: ...
    start: int
    end: int
    function: Symbol
    superblock: Optional[Block]
    global_block: Block
    static_block: Block
    is_global: bool
    is_static: bool


def lookup_symbol(name: str, block: Optional[Block] = None,
                  domain: Optional[DomainCategory] = None) -> Symbol: ...


def lookup_global_symbol(
    name: str, domain: Optional[DomainCategory] = None) -> Symbol: ...


def lookup_static_symbol(
    name: str, domain: Optional[DomainCategory] = None) -> Symbol: ...


class Symbol:
    type: Optional[Type]
    symtab: Symtab
    line: int
    name: str
    linkage_name: str
    print_name: str
    addr_class: SymbolAddress
    needs_frame: bool
    is_argument: bool
    is_constant: bool
    is_function: bool
    is_variable: bool

    def is_valid(self) -> bool: ...
    def value(self, frame: Optional[Frame] = None) -> Value: ...


DomainCategory = int

SYMBOL_UNDEF_DOMAIN: DomainCategory
SYMBOL_VAR_DOMAIN: DomainCategory
SYMBOL_STRUCT_DOMAIN: DomainCategory
SYMBOL_LABEL_DOMAIN: DomainCategory
SYMBOL_MODULE_DOMAIN: DomainCategory
SYMBOL_COMMON_BLOCK_DOMAIN: DomainCategory


SymbolAddress = int

SYMBOL_LOC_UNDEF: SymbolAddress
SYMBOL_LOC_CONST: SymbolAddress
SYMBOL_LOC_STATIC: SymbolAddress
SYMBOL_LOC_REGISTER: SymbolAddress
SYMBOL_LOC_ARG: SymbolAddress
SYMBOL_LOC_REF_ARG: SymbolAddress
SYMBOL_LOC_REGPARM_ADDR: SymbolAddress
SYMBOL_LOC_LOCAL: SymbolAddress
SYMBOL_LOC_TYPEDEF: SymbolAddress
SYMBOL_LOC_BLOCK: SymbolAddress
SYMBOL_LOC_CONST_BYTES: SymbolAddress
SYMBOL_LOC_UNRESOLVED: SymbolAddress
SYMBOL_LOC_OPTIMIZED_OUT: SymbolAddress
SYMBOL_LOC_COMPUTED: SymbolAddress
SYMBOL_LOC_COMPUTED: SymbolAddress


class Symtab_and_line:
    symtab: Symtab
    pc: int
    last: int
    line: int
    def is_valid(self) -> bool: ...


class Symtab:
    filename: str
    objfile: Objfile
    producer: str
    def is_valid(self) -> bool: ...
    def fullname(self) -> str: ...

    def global_block(self) -> Block: ...
    def static_block(self) -> Block: ...
    def linetable(self) -> LineTableEntry: ...


class LineTableEntry:
    line: int
    pc: int


class LineTable:
    def line(self, line: int) -> List[LineTableEntry]: ...
    def has_line(self, line: int) -> bool: ...
    def source_lines(self) -> List[int]: ...


BreakpointType = int

BP_BREAKPOINT: BreakpointType
BP_WATCHPOINT: BreakpointType
BP_HARDWARE_WATCHPOINT: BreakpointType
BP_READ_WATCHPOINT: BreakpointType
BP_ACCESS_WATCHPOINT: BreakpointType


WatchpointType = int

WP_READ: WatchpointType
WP_WRITE: WatchpointType
WP_ACCESS: WatchpointType


class Breakpoint:
    @overload
    def __init__(self, spec: str, type: Optional[BreakpointType] = None, wp_class: Optional[WatchpointType] = ...,
                 internal: bool = False, temporary: bool = False, qualified: bool = False): ...

    @overload
    def __init__(self, source: Optional[str] = None, function: Optional[str] = None, label: Optional[str] = None, line: Optional[int] = None,
                 internal: bool = False, temporary: bool = False, qualified: bool = False): ...

    def stop(self) -> None: ...

    def is_valid(self) -> bool: ...
    def delete(self) -> None: ...
    enabled: bool
    silent: bool
    pending: bool

    thread: Optional[int]
    task: Optional[int]
    ignore_count: int
    number: int
    type: BreakpointType
    visible: bool
    temporary: bool
    location: Optional[str]
    expression: Optional[str]
    condition: Optional[str]
    commands: Optional[str]


class FinishBreakpoint:
    def __init__(self, frame: Optional[Frame]
                 = None, internal: bool = False): ...

    def out_of_scope(self): ...
    return_value: Optional[Value]


class LazyString:
    def value(self) -> Value: ...
    address: int
    length: int
    encoding: str
    type: Type


class Architecture:
    def name(self) -> str: ...

    def disassemble(self, start_pc: int, end_pc: Optional[int] = None,
                    count: Optional[int] = None) -> dict: ...
