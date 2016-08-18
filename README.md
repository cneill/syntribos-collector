# Syntribos Template Collector

## Description

This is an mitmproxy in-line script to capture proxied requests and generate a
set of Syntribos request templates. It attempts to de-duplicate requests
intelligently (i.e. comparing HTTP method, set of URL query parameter names,
etc.)

## Dependencies

- [mitmproxy / mitmdump](https://mitmproxy.org/)

## Configuration

- `header_transforms` is a dictionary of header names and replacement values;
    this can be used, for example, to remove actual X-Auth-Token headers and
    replace them with `CALL_EXTERNAL` syntax
- `hosts` is a list of host:port strings (port not needed on 80/443) to collect
    requests to

## Usage

First, set up mitmproxy to listen and run the collector script

```
mitmproxy -p [port] -s "collector.py [output directory]"
OR
mitmdump -p [port] -s "collector.py [output directory]"
```

Next, set environment variables in your terminal to set your proxy:

```
export https_proxy="https://127.0.0.1:[port]"
export http_proxy="http://127.0.0.1:[port]"
```

Now run your functional tests from that terminal session, piping the requests 
through mitmproxy.

Finally, when you're done running your test, kill mitmproxy/mitmdump, and
your de-duped templates will be written out to the output directory you
specified when calling the collector script.
