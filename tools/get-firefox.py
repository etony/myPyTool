# -*- coding: utf-8 -*-
"""
Created on Wed Nov  9 14:16:53 2022

@author: admin
"""

import os
import sys
from configparser import ConfigParser
import ctypes as ct
import platform
from getpass import getpass
from base64 import b64decode
from typing import Optional, Any
import shutil
import json
import time

VERBOSE = False
SYSTEM = platform.system()
SYS64 = sys.maxsize > 2**32
DEFAULT_ENCODING = "utf-8"


class Exit(Exception):
    """Exception to allow a clean exit from any point in execution
    """
    CLEAN = 0
    ERROR = 1
    MISSING_PROFILEINI = 2
    MISSING_SECRETS = 3
    BAD_PROFILEINI = 4
    LOCATION_NO_DIRECTORY = 5
    BAD_SECRETS = 6
    BAD_LOCALE = 7

    FAIL_LOCATE_NSS = 10
    FAIL_LOAD_NSS = 11
    FAIL_INIT_NSS = 12
    FAIL_NSS_KEYSLOT = 13
    FAIL_SHUTDOWN_NSS = 14
    BAD_MASTER_PASSWORD = 15
    NEED_MASTER_PASSWORD = 16

    PASSSTORE_NOT_INIT = 20
    PASSSTORE_MISSING = 21
    PASSSTORE_ERROR = 22

    READ_GOT_EOF = 30
    MISSING_CHOICE = 31
    NO_SUCH_PROFILE = 32

    UNKNOWN_ERROR = 100
    KEYBOARD_INTERRUPT = 102

    def __init__(self, exitcode):
        self.exitcode = exitcode

    def __unicode__(self):
        return f"Premature program exit with exit code {self.exitcode}"


class c_char_p_fromstr(ct.c_char_p):
    """ctypes char_p override that handles encoding str to bytes"""

    def from_param(self):
        return self.encode(DEFAULT_ENCODING)


def ask_password(profile: str, interactive: bool) -> str:
    """
    Prompt for profile password
    """
    passwd: str
    passmsg = f"\nMaster Password for profile {profile}: "

    if sys.stdin.isatty() and interactive:
        passwd = getpass(passmsg)
    else:
        sys.stderr.write("Reading Master password from standard input:\n")
        sys.stderr.flush()
        # Ability to read the password from stdin (echo "pass" | ./firefox_...)
        passwd = sys.stdin.readline().rstrip("\n")

    return passwd


class NSSProxy:
    class SECItem(ct.Structure):
        """struct needed to interact with libnss
        """
        _fields_ = [
            ('type', ct.c_uint),
            ('data', ct.c_char_p),  # actually: unsigned char *
            ('len', ct.c_uint),
        ]

        def decode_data(self):
            _bytes = ct.string_at(self.data, self.len)
            return _bytes.decode(DEFAULT_ENCODING)

    class PK11SlotInfo(ct.Structure):
        """Opaque structure representing a logical PKCS slot
        """

    def __init__(self):
        # Locate libnss and try loading it
        self.libnss = load_libnss()

        SlotInfoPtr = ct.POINTER(self.PK11SlotInfo)
        SECItemPtr = ct.POINTER(self.SECItem)

        self._set_ctypes(ct.c_int, "NSS_Init", c_char_p_fromstr)
        self._set_ctypes(ct.c_int, "NSS_Shutdown")
        self._set_ctypes(SlotInfoPtr, "PK11_GetInternalKeySlot")
        self._set_ctypes(None, "PK11_FreeSlot", SlotInfoPtr)
        self._set_ctypes(ct.c_int, "PK11_NeedLogin", SlotInfoPtr)
        self._set_ctypes(ct.c_int, "PK11_CheckUserPassword",
                         SlotInfoPtr, c_char_p_fromstr)
        self._set_ctypes(ct.c_int, "PK11SDR_Decrypt",
                         SECItemPtr, SECItemPtr, ct.c_void_p)
        self._set_ctypes(None, "SECITEM_ZfreeItem", SECItemPtr, ct.c_int)

        # for error handling
        self._set_ctypes(ct.c_int, "PORT_GetError")
        self._set_ctypes(ct.c_char_p, "PR_ErrorToName", ct.c_int)
        self._set_ctypes(ct.c_char_p, "PR_ErrorToString",
                         ct.c_int, ct.c_uint32)

    def _set_ctypes(self, restype, name, *argtypes):
        """Set input/output types on libnss C functions for automatic type casting
        """
        res = getattr(self.libnss, name)
        res.argtypes = argtypes
        res.restype = restype

        # Transparently handle decoding to string when returning a c_char_p
        if restype == ct.c_char_p:
            def _decode(result, func, *args):
                return result.decode(DEFAULT_ENCODING)
            res.errcheck = _decode

        setattr(self, "_" + name, res)

    def initialize(self, profile: str):
        # The sql: prefix ensures compatibility with both
        # Berkley DB (cert8) and Sqlite (cert9) dbs
        profile_path = "sql:" + profile
        err_status: int = self._NSS_Init(profile_path)

        if err_status:
            self.handle_error(
                Exit.FAIL_INIT_NSS,
                "Couldn't initialize NSS, maybe '%s' is not a valid profile?",
                profile,
            )

    def shutdown(self):
        err_status: int = self._NSS_Shutdown()

        if err_status:
            self.handle_error(
                Exit.FAIL_SHUTDOWN_NSS,
                "Couldn't shutdown current NSS profile",
            )

    def authenticate(self, profile, interactive):
        """Unlocks the profile if necessary, in which case a password
        will prompted to the user.
        """
        keyslot = self._PK11_GetInternalKeySlot()

        if not keyslot:
            self.handle_error(
                Exit.FAIL_NSS_KEYSLOT,
                "Failed to retrieve internal KeySlot",
            )

        try:
            if self._PK11_NeedLogin(keyslot):
                password: str = ask_password(profile, interactive)

                err_status: int = self._PK11_CheckUserPassword(
                    keyslot, password)

                if err_status:
                    self.handle_error(
                        Exit.BAD_MASTER_PASSWORD,
                        "Master password is not correct",
                    )

            else:
                pass
        finally:
            # Avoid leaking PK11KeySlot
            self._PK11_FreeSlot(keyslot)

    def handle_error(self, exitcode: int, *logerror: Any):
        """If an error happens in libnss, handle it and print some debug information
        """

        code = self._PORT_GetError()
        name = self._PR_ErrorToName(code)
        name = "NULL" if name is None else name

        raise Exit(exitcode)

    def decrypt(self, data64):
        data = b64decode(data64)
        inp = self.SECItem(0, data, len(data))
        out = self.SECItem(0, None, 0)

        err_status: int = self._PK11SDR_Decrypt(inp, out, None)

        try:
            if err_status:  # -1 means password failed, other status are unknown
                self.handle_error(
                    Exit.NEED_MASTER_PASSWORD,
                    "Password decryption failed. Passwords protected by a Master Password!",
                )

            res = out.decode_data()
        finally:
            # Avoid leaking SECItem
            self._SECITEM_ZfreeItem(out, 0)

        return res



def load_libnss():
    """Load libnss into python using the CDLL interface
    """
    if SYSTEM == "Windows":
        nssname = "nss3.dll"
        locations: list[str] = [
            "",  # Current directory or system lib finder
            os.path.expanduser("~\\AppData\\Local\\Mozilla Firefox"),
            os.path.expanduser("~\\AppData\\Local\\Firefox Developer Edition"),
            os.path.expanduser("~\\AppData\\Local\\Mozilla Thunderbird"),
            os.path.expanduser("~\\AppData\\Local\\Nightly"),
            os.path.expanduser("~\\AppData\\Local\\SeaMonkey"),
            os.path.expanduser("~\\AppData\\Local\\Waterfox"),
            "C:\\Program Files\\Mozilla Firefox",
            "C:\\Program Files\\Firefox Developer Edition",
            "C:\\Program Files\\Mozilla Thunderbird",
            "C:\\Program Files\\Nightly",
            "C:\\Program Files\\SeaMonkey",
            "C:\\Program Files\\Waterfox",
        ]
        if not SYS64:
            locations = [
                "",  # Current directory or system lib finder
                "C:\\Program Files (x86)\\Mozilla Firefox",
                "C:\\Program Files (x86)\\Firefox Developer Edition",
                "C:\\Program Files (x86)\\Mozilla Thunderbird",
                "C:\\Program Files (x86)\\Nightly",
                "C:\\Program Files (x86)\\SeaMonkey",
                "C:\\Program Files (x86)\\Waterfox",
            ] + locations

        # If either of the supported software is in PATH try to use it
        software = ["firefox", "thunderbird", "waterfox", "seamonkey"]
        for binary in software:
            location: Optional[str] = shutil.which(binary)
            if location is not None:
                nsslocation: str = os.path.join(
                    os.path.dirname(location), nssname)
                locations.append(nsslocation)

    elif SYSTEM == "Darwin":
        nssname = "libnss3.dylib"
        locations = (
            "",  # Current directory or system lib finder
            "/usr/local/lib/nss",
            "/usr/local/lib",
            "/opt/local/lib/nss",
            "/sw/lib/firefox",
            "/sw/lib/mozilla",
            "/usr/local/opt/nss/lib",  # nss installed with Brew on Darwin
            "/opt/pkg/lib/nss",  # installed via pkgsrc
            "/Applications/Firefox.app/Contents/MacOS",  # default manual install location
            "/Applications/Thunderbird.app/Contents/MacOS",
            "/Applications/SeaMonkey.app/Contents/MacOS",
            "/Applications/Waterfox.app/Contents/MacOS",
        )

    else:
        nssname = "libnss3.so"
        if SYS64:
            locations = (
                "",  # Current directory or system lib finder
                "/usr/lib64",
                "/usr/lib64/nss",
                "/usr/lib",
                "/usr/lib/nss",
                "/usr/local/lib",
                "/usr/local/lib/nss",
                "/opt/local/lib",
                "/opt/local/lib/nss",
                os.path.expanduser("~/.nix-profile/lib"),
            )
        else:
            locations = (
                "",  # Current directory or system lib finder
                "/usr/lib",
                "/usr/lib/nss",
                "/usr/lib32",
                "/usr/lib32/nss",
                "/usr/lib64",
                "/usr/lib64/nss",
                "/usr/local/lib",
                "/usr/local/lib/nss",
                "/opt/local/lib",
                "/opt/local/lib/nss",
                os.path.expanduser("~/.nix-profile/lib"),
            )

    # If this succeeds libnss was loaded
    return find_nss(locations, nssname)


def find_nss(locations, nssname) -> ct.CDLL:
    """Locate nss is one of the many possible locations
    """
    fail_errors: list[tuple[str, str]] = []

    OS = ("Windows", "Darwin")

    for loc in locations:
        nsslib = os.path.join(loc, nssname)

        if SYSTEM in OS:
            # On windows in order to find DLLs referenced by nss3.dll
            # we need to have those locations on PATH
            os.environ["PATH"] = ';'.join([loc, os.environ["PATH"]])

            # However this doesn't seem to work on all setups and needs to be
            # set before starting python so as a workaround we chdir to
            # Firefox's nss3.dll/libnss3.dylib location
            if loc:
                if not os.path.isdir(loc):
                    # No point in trying to load from paths that don't exist
                    continue

                workdir = os.getcwd()
                os.chdir(loc)

        try:
            nss: ct.CDLL = ct.CDLL(nsslib)
        except OSError as e:
            fail_errors.append((nsslib, str(e)))
        else:

            return nss
        finally:
            if SYSTEM in OS and loc:
                # Restore workdir changed above
                os.chdir(workdir)

    else:

        for target, error in fail_errors:
            pass

        raise Exit(Exit.FAIL_LOCATE_NSS)


class FireFoxPasswd(object):
    def __init__(self):
        pass
    
    def get_firefox_passwd(self):
        basepath = os.path.join(os.environ['APPDATA'], "Mozilla", "Firefox")


        profileini = os.path.join(basepath, "profiles.ini")
        print(profileini)


        profiles = ConfigParser()
        profiles.read(profileini)

        sections = {}
        i = 1
        for section in profiles.sections():
            if section.startswith("Profile"):
                sections[str(i)] = profiles.get(section, "Path")
                i += 1

        print(sections)
        profile = os.path.join(basepath, sections["1"])
        print(profile)

        proxy = NSSProxy()
        proxy.initialize(profile)

        proxy.authenticate(profile, True)
        # print(os.path.expanduser("~admin"))

        db = os.path.join(profile, "logins.json")
        loginpass = []
        with open(db) as fh:
            data = json.load(fh)
            logins = data["logins"]

            for i in logins:
                user = proxy.decrypt(i["encryptedUsername"])
                passw = proxy.decrypt(i["encryptedPassword"])
                loginpass.append({"hostname":i["hostname"], "username":user, "password":passw, "encType":i["encType"],"timeCreated":time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i["timeCreated"]/1000)),"timeLastUsed":time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i["timeLastUsed"]/1000))})

        return loginpass
        


# basepath = os.path.join(os.environ['APPDATA'], "Mozilla", "Firefox")


# profileini = os.path.join(basepath, "profiles.ini")
# print(profileini)


# profiles = ConfigParser()
# profiles.read(profileini)

# sections = {}
# i = 1
# for section in profiles.sections():
#     if section.startswith("Profile"):
#         sections[str(i)] = profiles.get(section, "Path")
#         i += 1

# print(sections)
# profile = os.path.join(basepath, sections["1"])
# print(profile)

# proxy = NSSProxy()
# proxy.initialize(profile)

# proxy.authenticate(profile, True)
# # print(os.path.expanduser("~admin"))

# db = os.path.join(profile, "logins.json")
# loginpass = []
# with open(db) as fh:
#     data = json.load(fh)
#     logins = data["logins"]

#     for i in logins:
#         user = proxy.decrypt(i["encryptedUsername"])
#         passw = proxy.decrypt(i["encryptedPassword"])
#         loginpass.append({"hostname":i["hostname"], "username":user, "password":passw, "encType":i["encType"],"timeCreated":time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i["timeCreated"]/1000)),"timeLastUsed":time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i["timeLastUsed"]/1000))})

ff = FireFoxPasswd()
loginpass = ff.get_firefox_passwd()

for apass in loginpass:
    print("hostname:"+apass["hostname"])
    print("username:"+apass["username"])
    print("password:"+apass["password"])
    print("timeCreated:"+apass["timeCreated"])
    print("timeLastUsed:"+apass["timeLastUsed"])
    print("*"*30)
