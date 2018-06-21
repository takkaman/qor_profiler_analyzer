#!/bin/csh -f
sed -i 's/#username = request.remote_user/username = request.remote_user/' qor_web.py
sed -i 's/username = "phyan"/#username = "phyan"/' qor_web.py
