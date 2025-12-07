#!/usr/bin/env python3

import argparse
import base64
import importlib.metadata
import io
import os
import sys

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

from . import strings
from .bundled_adb import fastboot, usb_exceptions


class OemIdToken:
    # Callback object for fastboot 'get_identifier_token' command

    def __init__(self):
        self.n = 0
        self.id = None

    # Gets passed a FastbootMessage object
    def __call__(self, fb_msg):
        if self.n == 1 and self.id is None and fb_msg.header == b'INFO':
            self.id = fb_msg.message.decode('utf-8').strip()

        self.n += 1


class BootloaderCmd:
    def __init__(self):
        self.dev = None

    @staticmethod
    def sign_token(tok, key_file):
        priv_key = RSA.importKey(open(key_file).read())
        h = SHA256.new(tok)
        signature = PKCS1_v1_5.new(priv_key).sign(h)
        return signature

    def prepare(self):
        try:
            self.dev = fastboot.FastbootCommands()
            self.dev.ConnectDevice()
        except usb_exceptions.DeviceNotFoundError as e:
            print(strings.NO_DEVICE_FOUND.format(e), file=sys.stderr)
            sys.exit(1)
        except usb_exceptions.CommonUsbError as e:
            print(strings.COULD_NOT_CONNECT.format(e), file=sys.stderr)
            sys.exit(1)

        oem_id = OemIdToken()
        try:
            self.dev.Oem('get_identifier_token', info_cb=oem_id)
        except Exception as e:
            print(strings.FASTBOOT_ERROR.format(str(e)))
            sys.exit(1)

        print(strings.OEM_ID.format(oem_id.id))
        token_id = oem_id.id.ljust(2 * 64, '0')
        id_raw = base64.b16decode(token_id, casefold=True)
        pemfile = os.path.join(
            os.path.dirname(__file__),
            'rsa4096_vbmeta.pem'
        )
        sgn = self.sign_token(id_raw, pemfile)

        print(strings.DOWNLOAD_SIGNATURE)
        self.dev.Download(io.BytesIO(sgn), source_len=len(sgn))


class BootloaderUnlock(BootloaderCmd):
    def __call__(self):
        print(strings.PREPARING_TO_UNLOCK)
        self.prepare()

        print(strings.UNLOCK_INSTRUCTIONS)
        self.dev._SimpleCommand(
            b'flashing unlock_bootloader', timeout_ms=60*1000)

        print(strings.BOOTLOADER_UNLOCKED)
        self.dev.Close()


class BootloaderLock(BootloaderCmd):
    def __call__(self):
        print(strings.PREPARING_TO_LOCK)
        self.prepare()

        print(strings.LOCK_INSTRUCTIONS)
        self.dev._SimpleCommand(
            b'flashing lock_bootloader', timeout_ms=60*1000)

        print(strings.BOOTLOADER_LOCKED)
        self.dev.Close()


def main():
    parser = argparse.ArgumentParser(
        description=strings.DESCRIPTION
    )
    parser.add_argument('command',
                        type=str,
                        nargs='?',
                        help=strings.COMMAND_HELP
                        )
    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s ' +
                        importlib.metadata.version('unisoc-unlock')
                        )

    args = parser.parse_args()

    if args.command == 'lock':
        cmd = BootloaderLock()
    elif args.command in ['unlock', None]:
        cmd = BootloaderUnlock()
    else:
        print(strings.UNKNOWN_COMMAND.format(args.command), file=sys.stderr)
        sys.exit(1)

    cmd()


if __name__ == '__main__':
    main()
