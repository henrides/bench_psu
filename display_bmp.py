import wx
import time

class DisplayBmpFrame(wx.Frame):
    def __init__(self, parent, title, path):
        wx.Frame.__init__(self, parent, title=title)
        self._panel = wx.Panel(self)
        self._path = path

        bitmap = wx.Bitmap()
        bitmap.LoadFile(self._path)
        self._imageCtrl = wx.StaticBitmap(self._panel, wx.ID_ANY, bitmap)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self._imageCtrl, 0, wx.ALL, 5)
        self._panel.SetSizer(sizer)
        sizer.Fit(self)

        self._timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._handle_timer, self._timer)

        self._imageCtrl.Bind(wx.EVT_LEFT_DOWN, self._handle_click, self._imageCtrl)

        self._panel.Layout()
        print('init done')
        self.Show()
        self._timer.Start(1000)

    def _handle_timer(self, event):
        bitmap = wx.Bitmap()
        bitmap.LoadFile(self._path)
        self._imageCtrl = wx.StaticBitmap(self._panel, wx.ID_ANY, bitmap)

    def _handle_click(self, event):
        point = event.GetPosition()
        if point.x < 64:
            self._set_pin(8, 1)
            time.sleep(0.060)
            self._set_pin(8, 0)
        else:
            self._set_pin(9, 1)
            time.sleep(1.2)
            self._set_pin(9, 0)


    def _set_pin(self, pin, v):
        f = open('sim/pin{}'.format(pin), 'w')
        f.write(str(v))
        f.close()

app = wx.App(False)
frame = DisplayBmpFrame(None, title='Channel', path='./sim/display.bmp')
app.MainLoop()
