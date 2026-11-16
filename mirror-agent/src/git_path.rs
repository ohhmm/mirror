//! Lossless conversion of Git's NUL-delimited filename bytes to native paths.

use std::io;
use std::path::Path;

pub(crate) fn from_bytes(bytes: &[u8]) -> io::Result<&Path> {
    #[cfg(unix)]
    {
        use std::ffi::OsStr;
        use std::os::unix::ffi::OsStrExt;

        Ok(Path::new(OsStr::from_bytes(bytes)))
    }
    #[cfg(not(unix))]
    {
        std::str::from_utf8(bytes)
            .map(Path::new)
            .map_err(|error| io::Error::new(io::ErrorKind::InvalidData, error))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn preserves_unicode_and_whitespace() {
        let name = "directory/\u{e9}\u{96ea}\u{1f980} file\tline\n";
        assert_eq!(from_bytes(name.as_bytes()).unwrap(), Path::new(name));
    }

    #[test]
    fn preserves_replacement_characters() {
        let name = "directory/\u{fffd}";
        assert_eq!(from_bytes(name.as_bytes()).unwrap(), Path::new(name));
    }

    #[test]
    fn handles_non_utf8_without_substitution() {
        let bytes = b"directory/\xff";
        #[cfg(unix)]
        assert_eq!(
            from_bytes(bytes).unwrap().as_os_str().as_encoded_bytes(),
            bytes
        );
        #[cfg(not(unix))]
        assert_eq!(
            from_bytes(bytes).unwrap_err().kind(),
            io::ErrorKind::InvalidData
        );
    }
}
