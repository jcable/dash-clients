# dash-clients

A repository to contain MPEG-DASH clients for specific purposes.

First on the block is bbcaod.py - a Gstreamer python3 client.

Call on the command line with

bbcaod.py service programme

For example

    bbcaod.py worldservice "BBC News"
    bbyaod.py radio4 "The Film Programme"

bbcimda.py plays live streams. For example:

    bbcimda.py bbc_world_service
