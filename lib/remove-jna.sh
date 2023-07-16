#!/bin/bash

unzip -Z1 CookieMonster-no-jna.jar | grep "^com/sun" | xargs zip -d CookieMonster-no-jna.jar