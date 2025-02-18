"""
Print a list of symbols in the GOT and the files that provide them.

Errors will be printed if a symbol is provided by multiple shared
libraries, or if a symbol points to a library that doesn't export
it.
"""

__AUTHOR__ = "gordonmessmer"
__VERSION__ = 1.0
__LICENSE__ = "MIT"

import collections
import pathlib
from typing import TYPE_CHECKING

import gdb

if TYPE_CHECKING:
    from . import *
    from . import gdb

@register
class GotAuditCommand(GotCommand, GenericCommand):
    """Display current status of the got inside the process with paths providing functions."""

    _cmdline_ = "got-audit"
    _syntax_ = f"{_cmdline_} [FUNCTION_NAME ...] "
    _example_ = "got-audit read printf exit"
    _symbols_: dict[str, list[str]] = collections.defaultdict(list)
    _paths_: dict[str, list[str]] = collections.defaultdict(list)

    _expected_dups_ = {
        "__cxa_finalize",

        # Symbols that appear in both GNU's libc.so and libm.so
        "copysign", "copysignf", "copysignl", "__finite", "finite",
        "__finitef", "finitef", "__finitel", "finitel", "frexp",
        "frexpf", "frexpl", "ldexp", "ldexpf", "ldexpl", "modf",
        "modff", "modfl", "scalbn", "scalbnf", "scalbnl", "__signbit",
        "__signbitf", "__signbitl",

        # Symbols that appear in both GNU's libc.so and libattr.so
        "fgetxattr", "flistxattr", "fremovexattr", "fsetxattr",
        "getxattr", "lgetxattr", "listxattr", "llistxattr",
        "lremovexattr", "lsetxattr", "removexattr", "setxattr",

        # Symbols that appear in both GNU's libc.so and libtirpc.so
        "authdes_create", "authdes_pk_create", "_authenticate",
        "authnone_create", "authunix_create",
        "authunix_create_default", "bindresvport", "callrpc",
        "clnt_broadcast", "clnt_create", "clnt_pcreateerror",
        "clnt_perrno", "clnt_perror", "clntraw_create",
        "clnt_spcreateerror", "clnt_sperrno", "clnt_sperror",
        "clnttcp_create", "clntudp_bufcreate", "clntudp_create",
        "clntunix_create", "get_myaddress", "getnetname",
        "getpublickey", "getrpcport", "host2netname",
        "key_decryptsession", "key_decryptsession_pk",
        "key_encryptsession", "key_encryptsession_pk", "key_gendes",
        "key_get_conv", "key_secretkey_is_set", "key_setnet",
        "key_setsecret", "__libc_clntudp_bufcreate", "netname2host",
        "netname2user", "pmap_getmaps", "pmap_getport",
        "pmap_rmtcall", "pmap_set", "pmap_unset", "registerrpc",
        "_rpc_dtablesize", "rtime", "_seterr_reply", "svcerr_auth",
        "svcerr_decode", "svcerr_noproc", "svcerr_noprog",
        "svcerr_progvers", "svcerr_systemerr", "svcerr_weakauth",
        "svc_exit", "svcfd_create", "svc_getreq", "svc_getreq_common",
        "svc_getreq_poll", "svc_getreqset", "svcraw_create",
        "svc_register", "svc_run", "svc_sendreply", "svctcp_create",
        "svcudp_bufcreate", "svcudp_create", "svcunix_create",
        "svcunixfd_create", "svc_unregister", "user2netname",
        "xdr_accepted_reply", "xdr_array", "xdr_authunix_parms",
        "xdr_bool", "xdr_bytes", "xdr_callhdr", "xdr_callmsg",
        "xdr_char", "xdr_cryptkeyarg", "xdr_cryptkeyarg2",
        "xdr_cryptkeyres", "xdr_des_block", "xdr_double", "xdr_enum",
        "xdr_float", "xdr_free", "xdr_getcredres", "xdr_hyper",
        "xdr_int", "xdr_int16_t", "xdr_int32_t", "xdr_int64_t",
        "xdr_int8_t", "xdr_keybuf", "xdr_key_netstarg",
        "xdr_key_netstres", "xdr_keystatus", "xdr_long",
        "xdr_longlong_t", "xdrmem_create", "xdr_netnamestr",
        "xdr_netobj", "xdr_opaque", "xdr_opaque_auth", "xdr_pmap",
        "xdr_pmaplist", "xdr_pointer", "xdr_quad_t", "xdrrec_create",
        "xdrrec_endofrecord", "xdrrec_eof", "xdrrec_skiprecord",
        "xdr_reference", "xdr_rejected_reply", "xdr_replymsg",
        "xdr_rmtcall_args", "xdr_rmtcallres", "xdr_short",
        "xdr_sizeof", "xdrstdio_create", "xdr_string", "xdr_u_char",
        "xdr_u_hyper", "xdr_u_int", "xdr_uint16_t", "xdr_uint32_t",
        "xdr_uint64_t", "xdr_uint8_t", "xdr_u_long",
        "xdr_u_longlong_t", "xdr_union", "xdr_unixcred",
        "xdr_u_quad_t", "xdr_u_short", "xdr_vector", "xdr_void",
        "xdr_wrapstring", "xprt_register", "xprt_unregister",

        # Symbols that appear in libsasl2 and in its related libs
        "_plug_buf_alloc", "_plug_challenge_prompt", "_plug_decode",
        "_plug_decode_free", "_plug_decode_init", "_plug_find_prompt",
        "_plug_free_secret", "_plug_free_string",
        "_plug_get_error_message", "_plug_get_password",
        "_plug_get_realm", "_plug_get_simple", "_plug_iovec_to_buf",
        "_plug_ipfromstring", "_plug_make_fulluser",
        "_plug_make_prompts", "_plug_parseuser",
        "_plug_snprintf_os_info", "_plug_strdup",

        # Symbols that appear in libresolv and libvncserver
        "__b64_ntop", "__b64_pton",
    }

    def get_symbols_from_path(self, elf_file):
        nm = gef.session.constants["nm"]
        # retrieve symbols using nm
        lines = gef_execute_external([nm, "-D", elf_file], as_list=True)
        for line in lines:
            words = line.split()
            # Record the symbol if it is in the text section or
            # an indirect function or weak symbol
            if len(words) == 3 and words[-2] in ("T", "i", "I", "v", "V", "w", "W"):
                sym = words[-1].split("@")[0]
                if elf_file not in self._symbols_[sym]:
                    self._symbols_[sym].append(elf_file)
                self._paths_[elf_file].append(sym)

    @only_if_gdb_running
    def do_invoke(self, argv: list[str]) -> None:
        # Build a list of the symbols provided by each library path, and
        # a list of paths that provide each symbol.
        for section in gef.memory.maps:
            if (section.path not in self._paths_
                and pathlib.Path(section.path).is_file()
                and section.permission & Permission.EXECUTE):
                self.get_symbols_from_path(section.path)
        return super().do_invoke(argv)

    def build_line(self, name: str, path: str, color: str, address_val: int, got_address: int) -> str:
        line = Color.colorify(f"{name}", color)
        found = 0
        for section in gef.memory.maps:
            if not section.contains(got_address):
                continue
            line += f" : {section.path}"
            found = 1
            short_name = name.split("@")[0]
            # Symbol duplication isn't a strong signal for namespace tampering, but it should not be
            # allowed without review. Developers should register the symbols that multiple libraries
            # export. (Though the current implementation of hard-coding them in this tool should be
            # replaced with a more flexible approach.)
            if (len(self._symbols_[short_name]) > 1
                and short_name not in self._expected_dups_):
                line += f" :: ERROR {short_name} found in multiple paths ({str(self._symbols_[short_name])})"
            # Symbols within a Section are allowed to resolve to an address within the same Section.
            # This is usually an unresolved symbol.  In any case, we aren't concerned that a library
            # will subvert its own functionality through namespace tampering.
            if (section.path != "[vdso]"
                and section.path != path
                and short_name not in self._paths_[section.path]):
                line += f" :: ERROR {short_name} not exported by {section.path}"
            break
        if not found:
            line += " : no mapping found"
        return line
