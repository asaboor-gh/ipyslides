"""
Author Notes: Classes in this module should only be instantiated in Slides class or it's parent class
and then provided to other classes via composition, not inheritance.
"""

class Navigation:
    def __init__(self, _instanceSlides):
        "Instnace should be inside `Slides` class."
        self.slides = _instanceSlides
        self.widgets = self.slides.widgets
        self.wprogress = self.widgets.sliders.progress
        self.btn_next = self.widgets.buttons.next
        self.btn_prev = self.widgets.buttons.prev
        self.btn_panel = self.widgets.buttons.panel
        
        self.btn_prev.on_click(self._shift_left)
        self.btn_next.on_click(self._shift_right)
        self.btn_panel.on_click(self._toggle_panel)
        self.widgets.buttons.home.on_click(self._goto_home)
        self.widgets.buttons.end.on_click(self._goto_end)
        
    def _shift_right(self,change):
        self.widgets.slidebox.remove_class('Prev') # remove backwards animation safely
        if change and not self.slides._current.next_frame():
            if self.wprogress.value < self.wprogress.max:
                self.wprogress.value = self.wprogress.value + 1 # Forwards
            
    def _shift_left(self,change):
        self.widgets.slidebox.remove_class('Prev') # remove backwards animation safely
        if change and not self.slides._current.prev_frame():
            self.widgets.slidebox.add_class('Prev') # Backwards Animation
            if self.wprogress.value > 0:
                self.wprogress.value = self.wprogress.value - 1 # Backwards
    
    def _toggle_panel(self,change):
        if self.btn_panel.icon == 'plus':
            self.btn_panel.icon  = 'minus'
            self.btn_panel.tooltip = "Close Panel [S]"
            self.widgets.panelbox.layout.height = "100%"
            self.widgets.panelbox.layout.overflow = 'auto'
        else:
            self.btn_panel.icon = 'plus' #'ellipsis-v'
            self.btn_panel.tooltip = "Open Side Panel [S]"
            self.widgets.panelbox.layout.height = "0"
            self.widgets.panelbox.layout.overflow = 'hidden'
            
    def _goto_home(self,btn):
        try:
            self.wprogress.value = 0
            if self.widgets.buttons.toc.icon == 'minus':
                self.widgets.buttons.toc.click() # Close TOC but only if it was open, let other things work
        except:
            self.widgets._push_toast('Cannot go to home page. No slides found.')
            
    def _goto_end(self,btn):
        try:
            self.wprogress.value = self.wprogress.max
            if self.widgets.buttons.toc.icon == 'minus':
                self.widgets.buttons.toc.click() # Close TOC but only if it was open, let other things work
        except:
            self.widgets._push_toast('Cannot got to end of slides, may not enough slides exist.')