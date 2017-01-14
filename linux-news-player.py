import gi
import sys
import arrow
from struct import unpack, calcsize
gi.require_version('Gst', '1.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GObject, GLib, Gtk, Gst
# based on:
#   http://lzone.de/Media Player with GStreamer and PyGI
#   http://stackoverflow.com/questions/19332902/extract-historic-leap-seconds-from-tzdata

def get_leap(tzfile = '/usr/share/zoneinfo/right/UTC'):
    with open(tzfile, 'rb') as f:
        # read header
        fmt = '>4s c 15x 6l'
        (magic, format, ttisgmtcnt, ttisstdcnt,leapcnt, timecnt,
            typecnt, charcnt) =  unpack(fmt, f.read(calcsize(fmt)))
        assert magic == 'TZif'.encode('US-ASCII'), 'Not a timezone file'

        # skip over some uninteresting data
        fmt = '>%(timecnt)dl %(timecnt)dB %(ttinfo)s %(charcnt)ds' % dict(
            timecnt=timecnt, ttinfo='lBB'*typecnt, charcnt=charcnt)
        f.read(calcsize(fmt))

        #read leap-seconds
        fmt = '>2l'
        count = 0
        for i in range(leapcnt):
            tleap, nleap = unpack(fmt, f.read(calcsize(fmt)))
            dt = arrow.get(tleap-nleap+1)
            if dt < arrow.utcnow():
                count = count + 1
    return count

class PlaybackInterface:
    
    def __init__(self):
        self.playing = False
    
        # A free example sound track
        self.uri = "http://cdn02.cdn.gorillavsbear.net/wp-content/uploads/2012/10/GORILLA-VS-BEAR-OCTOBER-2012.mp3"
        self.uri = "http://a.files.bbci.co.uk/media/live/manifesto/audio/simulcast/dash/nonuk/dash_low/ak/bbc_world_service_news_internet.mpd"
    
        # GTK window and widgets
        self.window = Gtk.Window()
        self.window.set_size_request(300,50)
    
        vbox = Gtk.Box(Gtk.Orientation.HORIZONTAL, 0)
        vbox.set_margin_top(3)
        vbox.set_margin_bottom(3)
        self.window.add(vbox)
    
        self.playButtonImage = Gtk.Image()
        self.playButtonImage.set_from_stock("gtk-media-play", Gtk.IconSize.BUTTON)
        self.playButton = Gtk.Button.new()
        self.playButton.add(self.playButtonImage)
        self.playButton.connect("clicked", self.playToggled)
        Gtk.Box.pack_start(vbox, self.playButton, False, False, 0)
    
        self.slider = Gtk.HScale()
        self.slider.set_margin_left(6)
        self.slider.set_margin_right(6)
        self.slider.set_draw_value(False)
        self.slider.set_range(0, 100)
        self.slider.set_increments(1, 10)
    
        Gtk.Box.pack_start(vbox, self.slider, True, True, 0)
    
        self.label = Gtk.Label(label='00:00')
        self.label.set_margin_left(6)
        self.label.set_margin_right(6)
        Gtk.Box.pack_start(vbox, self.label, False, False, 0)
    
        self.window.show_all()
    
        # GStreamer Setup
        Gst.init_check(None)
        self.player = Gst.ElementFactory.make("playbin", "player")
        fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
        self.player.set_property("video-sink", fakesink)
        bus = self.player.get_bus()
        #bus.add_signal_watch_full()
        bus.connect("message", self.on_message)
        self.player.connect("about-to-finish",  self.on_finished)
    
    def on_message(self, bus, message):
        t = message.type
        if t == Gst.Message.EOS:
            self.player.set_state(Gst.State.NULL)
            self.playing = False
        elif t == Gst.Message.ERROR:
            self.player.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print("Error: %s" % err, debug)
            self.playing = False
        self.updateButtons()
    
    def on_finished(self, player):
        self.playing = False
        self.slider.set_value(0)
        self.label.set_text("00:00")
        self.updateButtons()
    
    def play(self):
        self.player.set_property("uri", self.uri)
        self.player.set_state(Gst.State.PLAYING)
        GObject.timeout_add(1000, self.updateSlider)
    
    def stop(self):
        self.player.set_state(Gst.State.NULL)
        
    def playToggled(self, w):
        self.slider.set_value(0)
        self.label.set_text("00:00")
    
        if(self.playing == False):
            self.play()
        else:
            self.stop()
    
        self.playing=not(self.playing)
        self.updateButtons()
    
    def updateSlider(self):
        if(self.playing == False):
           return False # cancel timeout
    
        try:
           nanosecs = self.player.query_position(Gst.Format.TIME)[1]
           duration_nanosecs = self.player.query_duration(Gst.Format.TIME)[1]
    
           # block seek handler so we don't seek when we set_value()
           # self.slider.handler_block_by_func(self.on_slider_change)
    
           duration = float(duration_nanosecs) / Gst.SECOND
           position = float(nanosecs) / Gst.SECOND
           self.slider.set_range(0, duration)
           self.slider.set_value(position)
           leap_seconds = get_leap()
           utc2tai = 10
           dt = arrow.get(position-leap_seconds-utc2tai)
           self.label.set_text (dt.format("YYYY-MM-DD HH:mm:ss"))
    
           #self.slider.handler_unblock_by_func(self.on_slider_change)
        
        except Exception as e:
            # pipeline must not be ready and does not know position
            print(e)
            pass
    
        return True
    
    def updateButtons(self):
            if(self.playing == False):
               self.playButtonImage.set_from_stock("gtk-media-play", Gtk.IconSize.BUTTON)
            else:
               self.playButtonImage.set_from_stock("gtk-media-stop", Gtk.IconSize.BUTTON)

if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    PlaybackInterface()
    Gtk.main()
