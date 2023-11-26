import anywidget
import traitlets
import ipywidgets as ipw
from pathlib import Path


class InteractionWidget(anywidget.AnyWidget):
    _esm =  (Path(__file__).with_name('js') / "interaction.js").read_text()
    msg_topy = traitlets.Unicode('').tag(sync=True)
    msg_tojs = traitlets.Unicode('').tag(sync=True)

    def __init__(self, _widgets, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._toggles = _widgets.toggles
        self._buttons = _widgets.buttons

    @traitlets.observe("msg_topy")
    def see_changes(self, change):
        msg = change.new
        if not msg:
            return # Message set empty
        if msg == 'TFS': 
            self._toggles.fscreen.value = not self._toggles.fscreen.value
        elif msg == 'NEXT':
            self._buttons.next.click()
        elif msg == 'PREV':
            self._buttons.prev.click()
        elif msg == 'TLSR':
            self._toggles.laser.value = not self._toggles.laser.value
        elif msg == 'ZOOM':
            self._toggles.zoom.value = not self._toggles.zoom.value
        elif msg == 'TPAN':
            self._buttons.setting.click()
        elif msg == 'SCAP':
            self._buttons.capture.click()
        elif msg == 'TVP' and not self._toggles.window.disabled:
            self._toggles.window.value = not self._toggles.window.value
        elif msg == 'NOVP': # Other than voila, no viewport button
            self._toggles.window.disabled = True
            self._toggles.window.layout.display = 'none'
        elif msg == 'LOADED':
            pass  # Some functionality may be needed

        self.msg_topy = "" # Reset for successive simliar changes
        self.msg_tojs = "" # Reset