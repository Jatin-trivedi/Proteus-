"""
Proteus JOCKY Forensic Runtime - Filesystem Forensic Collectors
Implements:
- filesystem.metadata(path)
- filesystem.hash(path)
"""

import os
import stat
import datetime
import hashlib
from typing import Dict, Any

try:
    from runtime.collector import BaseCollector
    from runtime.errors import CollectorException, ErrorCode
except ImportError:
    from collector import BaseCollector
    from errors import CollectorException, ErrorCode


def _validate_and_extract_path(parameters: Dict[str, Any], op_name: str) -> str:
    """Validates the 'path' parameter and returns the string path."""
    if "path" not in parameters or parameters["path"] is None:
        raise CollectorException(
            code=ErrorCode.INVALID_PARAMETERS,
            message=f"Missing required parameter 'path' for {op_name}"
        )

    path_val = parameters["path"]
    if not isinstance(path_val, str):
        raise CollectorException(
            code=ErrorCode.INVALID_PARAMETERS,
            message=f"Invalid path parameter: {path_val!r}. Expected a string."
        )

    if not path_val.strip():
        raise CollectorException(
            code=ErrorCode.INVALID_PARAMETERS,
            message=f"Parameter 'path' cannot be empty for {op_name}"
        )

    return path_val


class FilesystemMetadataCollector(BaseCollector):
    """
    Forensic collector for 'filesystem.metadata(path)'.
    Safely collects metadata for a file or directory:
    - path (str)
    - size (int)
    - creation_time (str)
    - modification_time (str)
    - access_time (str)
    - permissions (str)
    """

    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        path = _validate_and_extract_path(parameters, "filesystem.metadata")

        if not os.path.exists(path):
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message=f"Path not found: '{path}'"
            )

        try:
            st = os.stat(path)
            size = st.st_size

            # Modification and Access times
            mtime_str = datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            atime_str = datetime.datetime.fromtimestamp(st.st_atime).strftime("%Y-%m-%d %H:%M:%S")

            # Creation / Birth time (platform-aware)
            birthtime = getattr(st, "st_birthtime", getattr(st, "st_ctime", st.st_mtime))
            ctime_str = datetime.datetime.fromtimestamp(birthtime).strftime("%Y-%m-%d %H:%M:%S")

            # Octal permission string (e.g. "0644", "0755")
            perms_str = oct(st.st_mode & 0o777)[2:].zfill(4)

            return {
                "path": str(path),
                "size": int(size),
                "creation_time": ctime_str,
                "modification_time": mtime_str,
                "access_time": atime_str,
                "permissions": perms_str
            }
        except PermissionError:
            raise CollectorException(
                code=ErrorCode.PERMISSION_DENIED,
                message=f"Permission denied accessing metadata for path: '{path}'"
            )
        except CollectorException:
            raise
        except Exception as e:
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message=f"Failed to collect metadata for path '{path}': {e}"
            )


class FilesystemHashCollector(BaseCollector):
    """
    Forensic collector for 'filesystem.hash(path)'.
    Calculates the SHA-256 cryptographic digest of the target file in read-only mode.
    - path (str)
    - algorithm (str, "SHA-256")
    - hash (str)
    """

    def collect(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        path = _validate_and_extract_path(parameters, "filesystem.hash")

        if not os.path.exists(path):
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message=f"Path not found: '{path}'"
            )

        if os.path.isdir(path):
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message=f"Target path '{path}' is a directory. Cannot compute file hash directly."
            )

        try:
            sha256_hash = hashlib.sha256()
            with open(path, "rb") as f:
                while chunk := f.read(65536):
                    sha256_hash.update(chunk)

            return {
                "path": str(path),
                "algorithm": "SHA-256",
                "hash": sha256_hash.hexdigest()
            }
        except PermissionError:
            raise CollectorException(
                code=ErrorCode.PERMISSION_DENIED,
                message=f"Permission denied reading file for hash: '{path}'"
            )
        except CollectorException:
            raise
        except Exception as e:
            raise CollectorException(
                code=ErrorCode.COLLECTION_FAILED,
                message=f"Failed to calculate SHA-256 hash for '{path}': {e}"
            )
