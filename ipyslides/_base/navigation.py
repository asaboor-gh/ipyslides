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
        
        self.btn_prev.on_click(self._shift_left)
        self.btn_next.on_click(self._shift_right)
        
    def _shift_right(self,change):
        self.widgets.slidebox.remove_class('Prev') # remove backwards animation safely
        self.widgets.slidebox.remove_class('AnimPrev') # content animation flag
        if change and not self.slides._current.next_frame():
            if self.wprogress.value < self.wprogress.max:
                self.wprogress.value = self.wprogress.value + 1 # Forwards
            
    def _shift_left(self,change):
        self.widgets.slidebox.remove_class('Prev') # remove backwards animation safely, need trigger before adding
        if change and not self.slides._current.prev_frame():
            self.widgets.slidebox.add_class('Prev') # Backwards Animation
            self.widgets.slidebox.add_class('AnimPrev') # content animation flag, need to stay persistent to avoid trigger removal too early
            if self.wprogress.value > 0:
                self.wprogress.value = self.wprogress.value - 1 # Backwards
               