# Syntribos Template Collector

## Description

This is an mitmproxy in-line script to capture proxied requests and generate a set of Syntribos request templates. It attempts to de-duplicate requests intelligently (i.e. comparing HTTP method, set of URL query parameter names, etc.)

## Dependencies

- [mitmproxy / mitmdump](https://mitmproxy.org/)

## Configuration

- `header_transforms` is a dictionary of header names and replacement values; this can be used, for example, to remove actual X-Auth-Token headers and replace them with `CALL_EXTERNAL` syntax
- `hosts` is a list of host:port strings (port not needed on 80/443) to collect requests to

## Usage

```
mitmproxy -s "collector.py [output directory]"
OR
mitmdump -s "collector.py [output directory]"
```
