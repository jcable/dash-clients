#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
from xml.etree import ElementTree
from datetime import datetime
import arrow
from urllib.request import urlopen

Gst.init(None)

channel = sys.argv[1]
now = arrow.utcnow()
wanted = now.replace(weeks=-1)
with urlopen("http://www.bbc.co.uk/radio/imda/imda_transports.xml") as f:
    tree = ElementTree.parse(f)
for node in tree.find("brand/[@refid='%s']/transport/media[@type='dash']" % channel):
    url = node.attrib.get("url")
    break
# Build the pipeline
pipeline = Gst.parse_launch("playbin uri=%s" % url)

# Start playing
pipeline.set_state(Gst.State.PLAYING)

# Wait until error or EOS
bus = pipeline.get_bus()
msg = bus.timed_pop_filtered(
    Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)

# Free resources
pipeline.set_state(Gst.State.NULL)
