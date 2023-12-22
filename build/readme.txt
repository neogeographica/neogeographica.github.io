The old site-gen.py script was written back in the Python 2 days, and I don't
have a good reason to try to rewrite it from scratch. Especially because the
"postmarkup" module that it depends on is in turn dependent on a "parser"
module that has been removed from the latest versions of Python 3.

So, the coward's way out here is to just build it in a container:

* Use the build-container.sh script here to create the container image on the
local system.

* If the container image exists on the local system, use the build-site.sh
script to run site-gen.py.

This should have the same output as "natively" running site-gen.py with
Python 2. The only difference is that it will not be able to automatically
load the site in a web browser when it is finished.