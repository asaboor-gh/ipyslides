"""
Author Notes: Classes in this module should only be instantiated in LiveSlide class or it's parent class
and then provided to other classes via composition, not inheritance.
"""

class Navigation:
    def __init__(self, _instanceWidgets):
        "Both instnaces should be inside `LiveSlide` class."
        self.widgets = _instanceWidgets
        self.N = self.widgets.sliders.progress.max + 1
        self.prog_slider = self.widgets.sliders.progress
        self.btn_next = self.widgets.buttons.next
        self.btn_prev = self.widgets.buttons.prev
        self.btn_setting = self.widgets.buttons.setting
        self.visible_slider = self.widgets.sliders.visible
    
        
        self.btn_prev.on_click(self.__shift_left)
        self.btn_next.on_click(self.__shift_right)
        self.btn_setting.on_click(self.__toggle_panel)
        self.visible_slider.observe(self.__set_hidden_height,names=['value'])
        
    def __shift_right(self,change):
        if change:
            if self.prog_slider.value >= self.prog_slider.max:
                self.prog_slider.value = 0 # switch  to title back
            else:
                self.prog_slider.value = self.prog_slider.value + 1  
    
    def __shift_left(self,change):
        if change:
            if self.prog_slider.value <= 0:
                self.prog_slider.value = self.prog_slider.max # loop back to last slide
            else:
                self.prog_slider.value = self.prog_slider.value - 1
    
    def __toggle_panel(self,change):
        if self.btn_setting.description == '\u2630':
            self.btn_setting.description  = '⨉'
            self.widgets.panelbox.layout.display = 'flex'
            self.btn_next.disabled = True
            self.btn_prev.disabled = True
        else:
            self.btn_setting.description = '\u2630'
            self.widgets.panelbox.layout.display = 'none'
            self.btn_next.disabled = False
            self.btn_prev.disabled = False
            
    def __set_hidden_height(self,change):
        self.widgets.slidebox.layout.height = f'{self.visible_slider.value}%'
        self.widgets.slidebox.layout.margin='auto 4px'
        
        