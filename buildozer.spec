[app]
title = DBInputCPapp
package.name = dbinputcpapp
package.domain = org.example
source.dir = .
source.include_exts = py
version = 0.1

requirements = python3==3.12.12, kivy==2.3.0,

orientation = portrait
fullscreen = 0

p4a.branch = develop
android.api = 36
android.ndk = 29
android.archs = arm64-v8a

[buildozer]
warn_on_root = 1
log_level = 2
