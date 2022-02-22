"""
Author Notes: Classes in this module should only be instantiated in LiveSlide class or it's parent class
and then provided to other classes via composition, not inheritance.
"""

class Navigation:
    def __init__(self, _instanceWidgets):
        "Both instnaces should be inside `LiveSlide` class."
        self.widgets = _instanceWidgets
        self.N = self.widgets.sliders.progress.max + 1
        self.progress_slider = self.widgets.sliders.progress
        self.btn_next = self.widgets.buttons.next
        self.btn_prev = self.widgets.buttons.prev
        self.btn_settings = self.widgets.buttons.setting
        self.visible_slider = self.widgets.sliders.visible
    
        
        self.btn_prev.on_click(self.__shift_left)
        self.btn_next.on_click(self.__shift_right)
        self.btn_settings.on_click(self.__toggle_panel)
        self.visible_slider.observe(self.__set_hidden_height,names=['value'])
        
    def __shift_right(self,change):
        if change:
            if self.progress_slider.value >= self.progress_slider.max:
                self.progress_slider.value = 0 # switch  to title back
            else:
                self.progress_slider.value = self.progress_slider.value + 1  
    
    def __shift_left(self,change):
        if change:
            if self.progress_slider.value <= 0:
                self.progress_slider.value = self.progress_slider.max # loop back to last slide
            else:
                self.progress_slider.value = self.progress_slider.value - 1
    
    def __toggle_panel(self,change):
        if self.btn_settings.description == '\u2630':
            self.btn_settings.description  = '⨉'
            self.widgets.panelbox.layout.display = 'flex'
            self.btn_next.disabled = True
            self.btn_prev.disabled = True
        else:
            self.btn_settings.description = '\u2630'
            self.widgets.panelbox.layout.display = 'none'
            self.btn_next.disabled = False
            self.btn_prev.disabled = False
            
    def __set_hidden_height(self,change):
        self.widgets.slidebox.layout.height = f'{self.visible_slider.value}%'
        self.widgets.slidebox.layout.margin='auto 4px'
        
        